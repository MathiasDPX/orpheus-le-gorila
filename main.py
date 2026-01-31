import re
import duckdb
import traceback
from os import getenv
from slack_bolt import App
from dotenv import load_dotenv
from letterboxd import LetterboxdClient
from slack_bolt.adapter.socket_mode import SocketModeHandler

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
            """CREATE TABLE IF NOT EXISTS linked_accounts (
                slack_id TEXT PRIMARY KEY,
                boxd_username TEXT UNIQUE NOT NULL
            )"""
        )


def get_boxd_by_slack(slack_id: str):
    with duckdb.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT boxd_username FROM linked_accounts WHERE slack_id = ?", [slack_id]
        ).fetchone()
        return row[0] if row else None


def link_account(slack_id: str, boxd_username: str):
    with duckdb.connect(DB_PATH) as con:
        con.execute(
            """
            INSERT INTO linked_accounts (slack_id, boxd_username)
            VALUES (?, ?)
            ON CONFLICT (slack_id)
            DO UPDATE SET boxd_username = EXCLUDED.boxd_username
            """,
            [slack_id, boxd_username],
        )


BOXD_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{2,15}$")


@app.command("/boxd-link")
def repeat_text(ack, respond, command):
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
    
    slackid = command['user_id']
    user = boxd_client.get_member(boxdid)
    bio = user['bio']
    
    if slackid not in bio:
        respond(f"Make sure you put your Slack ID in your Letterboxd bio\n_tips: it's `{slackid}`_")
        return

    try:
        link_account(command["user_id"], boxdid)
        respond(
            f":hooray-wx: Successfully linked <@{slackid}> to `{username}`"
        )
    except:
        tb = traceback.format_exc()
        respond(f":panic-wx: Unable to link your account!\n```{tb}```")


if __name__ == "__main__":
    init_db()
    handler = SocketModeHandler(app)
    handler.start()
