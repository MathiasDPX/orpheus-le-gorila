from slack_bolt import App
from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App()

@app.command("/boxd-link")
def repeat_text(ack, respond, command):
    ack()
    print(command['text'])

if __name__ == "__main__":
    handler = SocketModeHandler(app)
    handler.start()