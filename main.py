import re
import duckdb
import traceback
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
DB_PATH = "database.db"


def init_db():
    with duckdb.connect(DB_PATH) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
                slack_id TEXT PRIMARY KEY,
                boxd_username TEXT UNIQUE NOT NULL,
                channel TEXT UNIQUE DEFAULT NULL,
                lastUpdate TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def get_boxd_by_slack(slack_id: str):
    with duckdb.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT boxd_username FROM accounts WHERE slack_id = ?", [slack_id]
        ).fetchone()
        return row[0] if row else None


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
    if boxdid == None:
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
        tb = traceback.format_exc()
        respond(f":panic-wx: Unable to link your account!\n```{tb}```")


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
        if boxd_id == None:
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


def star_to_text(rating):
    full_stars = int(rating // 1) * ":ms-star:"
    half_star = ":ms-half-star:" if rating % 1 == 0.5 else ""
    empty_stars = int((5 - rating) // 1) * ":ms-empty-star:"

    return full_stars + half_star + empty_stars


def post_activities():
    users = get_configured_users()
    for user in users:
        activities = boxd_client.get_activity(user[1])

        for activity in activities:
            if activity.whenCreated < user[3]:
                continue

            message = None
            member = activity.member
            if type(activity) == FollowActivity:
                message = f"{member.displayName} followed <https://letterboxd.com/{activity.followed.username}|{activity.followed.displayName}>"
            elif type(activity) == WatchlistActivity:
                if activity.film.adult:
                    continue

                filmName = activity.film.fullDisplayName or activity.film.name
                message = f"{member.displayName} added {filmName} to {member.pronoun.possessivePronoun} watchlist"
            elif type(activity) == DiaryEntryActivity:
                if activity.film.adult:
                    continue

                filmName = activity.film.fullDisplayName or activity.film.name

                liked = ":ms-red-heart: " if activity.like else ""
                stars = star_to_text(activity.rating)
                review = ""
                if activity.review != None:
                    review = (
                        shorten_text(activity.review.text)
                        if activity.review.containsSpoilers == False
                        else f"_This review contains spoilers_"
                    )
                    review = (
                        "\n> "
                        + html_to_mrkdwn(review)
                        + f"\nRead the <https://letterboxd.com/{member.username}/film/{activity.film.sortingName}/|review>"
                    )

                message = (
                    f"{member.displayName} watched {filmName}\n{liked}{stars}{review}"
                )

            if message == None:
                continue

            app.client.chat_postMessage(channel=user[2], text=message)

        update_lastUpdate(user[0])


if __name__ == "__main__":
    init_db()

    scheduler = BackgroundScheduler()
    scheduler.add_job(post_activities, "interval", minutes=30)
    scheduler.start()

    handler = SocketModeHandler(app)
    post_activities()
    handler.start()
