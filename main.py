import re
import blocks
import duckdb
from utils import *
from os import getenv
from slack_bolt import App
from dotenv import load_dotenv
from letterboxd import LetterboxdClient
from slack_bolt.adapter.socket_mode import SocketModeHandler
from apscheduler.schedulers.background import BackgroundScheduler
from schemas import FollowActivity, WatchlistActivity, DiaryEntryActivity

load_dotenv()

app = App()
boxd_client = LetterboxdClient(
    client_id=getenv("BOXD_CLIENT_ID"),
    client_secret=getenv("BOXD_CLIENT_SECRET"),
    username=getenv("BOXD_USERNAME"),
    password=getenv("BOXD_PASSWORD"),
)
DB_PATH = getenv("DATABASE_PATH", "database.db")


def init_db():
    with duckdb.connect(DB_PATH) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
                slack_id TEXT PRIMARY KEY,
                boxd_username TEXT UNIQUE NOT NULL,
                channel TEXT UNIQUE DEFAULT NULL,
                lastUpdate TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                events VARCHAR[] DEFAULT ['WatchlistActivity', 'DiaryEntryActivity']
            )"""
        )


def get_boxd_by_slack(slack_id: str):
    with duckdb.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT boxd_username FROM accounts WHERE slack_id = ?", [slack_id]
        ).fetchone()
        return row[0] if row else None


def get_user(slack_id: str):
    with duckdb.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE slack_id = ?", [slack_id]
        ).fetchone()
        return row if row else None

def link_account(slack_id: str, boxd_username: str):
    with duckdb.connect(DB_PATH) as con:
        con.execute(
            """
            INSERT INTO accounts (slack_id, boxd_username)
            VALUES (?, ?)
            ON CONFLICT (slack_id)
            DO UPDATE SET boxd_username = EXCLUDED.boxd_username
            """,
            [slack_id, boxd_username],
        )

def update_events_subscribe(events, slackid):
    with duckdb.connect(DB_PATH) as con:
        con.execute(
            "UPDATE accounts SET events=? WHERE slack_id=?", [events, slackid]
        )

def get_configured_users():
    with duckdb.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT * FROM accounts WHERE channel IS NOT NULL"
        ).fetchall()
        return rows if rows else []


def get_channel(slack_id):
    with duckdb.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT channel FROM accounts WHERE slack_id=?", [slack_id]
        ).fetchone()
        return row[0] if row else None


def set_channel(slack_id, channel):
    with duckdb.connect(DB_PATH) as con:
        con.execute(
            "UPDATE accounts SET channel=? WHERE slack_id=?", [channel, slack_id]
        )


def update_lastUpdate(slack_id):
    with duckdb.connect(DB_PATH) as con:
        con.execute(
            "UPDATE accounts SET lastUpdate = now() WHERE slack_id=?",
            [slack_id],
        )


BOXD_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{2,15}$")


@app.command("/boxd-info")
def boxd_infos(ack, respond, command):
    ack()
    
    user = get_user(command['user_id'])
    
    if user is None:
        respond("You need to link your Letterboxd account before using this\nUse: `/boxd-link [username]`")
        return
    
    app.client.views_open(
        trigger_id=command["trigger_id"], view=blocks.modal_info(user)
    )

@app.command("/boxd-events")
def boxd_events(ack, respond, command):
    ack()

    slackid = command["user_id"]
    user = get_user(slackid)

    if user is None:
        respond(
            "You need to link your Letterboxd account before using this\nUse: `/boxd-link [username]`"
        )
        return

    channel = get_channel(slackid)

    app.client.views_open(
        trigger_id=command["trigger_id"], view=blocks.modal_events(channel, user[4])
    )


@app.command("/boxd-link")
def boxd_link(ack, respond, command):
    ack()
    username: str = command["text"]
    username = username.strip()

    if not BOXD_USERNAME_PATTERN.match(username):
        respond(
            "This username doesn't seems valid\nTry only using letters, number and underscores"
        )
        return

    boxdid = boxd_client.get_id_by_username(username)
    if boxdid is None:
        respond(f":alibaba-search: Couldn't find any username named `{username}`")
        return

    slackid = command["user_id"]
    user = boxd_client.get_member(boxdid)
    bio = user["bio"]

    if slackid not in bio:
        respond(
            f"Make sure you put your Slack ID in your Letterboxd bio\n_tips: it's `{slackid}`_"
        )
        return

    try:
        link_account(command["user_id"], boxdid)
        respond(f":hooray-wx: Successfully linked <@{slackid}> to `{username}`")
    except:
        respond(f":panic-wx: Unable to link your account!")


@app.action("events-change")
def handle_events_change(ack, body, logger):
    ack()
    
    selected_options = []
    for action in body["actions"]:
        if action["action_id"] != "events-change":
            continue

        selected_options = [option['value'] for option in action["selected_options"]]
        
    user_id = body['user']['id']
    update_events_subscribe(selected_options, user_id)

@app.action("open_letterboxd")
def handle_letterboxd_button(ack):
    ack()


@app.command("/boxd-toggle")
def boxd_toggle(ack, respond, command):
    ack()
    state: str = command["text"].lower()
    slackid = command["user_id"]

    if state == "off":
        set_channel(slackid, None)
        respond("Letterboxd logging disabled")
    elif state == "on":
        boxd_id = get_boxd_by_slack(slackid)
        if boxd_id is None:
            respond(
                "Link your Letterboxd account before enabling logging\nUsing `/boxd-link [username]`"
            )
            return

        try:
            set_channel(slackid, command["channel_id"])
            respond("Enabled Letterboxd logging")
        except duckdb.ConstraintException:
            respond("This channel is already used by someone else")
    else:
        respond(
            "Unknown command, make sure to use on or off\nExample: `/boxd-toggle on`"
        )


def post_activities():
    users = get_configured_users()
    for user in users:
        activities = boxd_client.get_activity(user[1])

        for activity in activities:
            if activity.when_created < user[3]:
                continue

            blocks_message = None
            text_message = None
            member = activity.member
            subscribed_events = user[4]
            if isinstance(activity, FollowActivity) and "FollowActivity" in subscribed_events:
                text_message = f"{member.display_name} followed <https://letterboxd.com/{activity.followed.username}|{activity.followed.display_name}>"
                blocks_message = blocks.from_mrkdwn(text_message)

            elif isinstance(activity, WatchlistActivity) and "WatchlistActivity" in subscribed_events:
                if activity.film.adult:
                    continue

                filmName = activity.film.full_display_name or activity.film.name
                text_message = f"{member.display_name} added {filmName} to {member.pronoun.possessive_pronoun} watchlist"
                blocks_message = blocks.from_mrkdwn(text_message)

            elif isinstance(activity, DiaryEntryActivity) and "DiaryEntryActivity" in subscribed_events:
                if activity.film.adult:
                    continue

                text_message = f"{member.display_name} logged {activity.film.full_display_name or activity.film.name} ({activity.rating} stars)"
                blocks_message = blocks.from_diaryentry(activity)

            if blocks_message is None:
                continue

            app.client.chat_postMessage(
                channel=user[2], blocks=blocks_message, text=text_message
            )

        update_lastUpdate(user[0])


if __name__ == "__main__":
    init_db()

    scheduler = BackgroundScheduler()
    scheduler.add_job(post_activities, "interval", minutes=30)
    scheduler.start()

    handler = SocketModeHandler(app)
    post_activities()
    handler.start()
