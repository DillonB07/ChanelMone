import os
import requests

from dotenv import load_dotenv
from pyairtable import Api
from slack_bolt import App

load_dotenv()

api = Api(api_key=os.environ.get("AIRTABLE_ACCESS_TOKEN"))
table = api.table(os.environ.get("AIRTABLE_BASE_ID"), "Permissions")


# Initialize your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

def get_perms(channel_id, user_id):
    print(channel_id, user_id)

    # If user is workspace admin or owner, return all permissions
    # If not, return only the permissions for that channel
    


    # get the first record with the channel id. Channel ID is unique so this will never be more than one record so first is fine
    perms = table.first(formula=f"{{Channel ID}} = '{channel_id}'")
    print(perms)
    fields = perms.get("fields")
    return {
        "Ping Channel": fields.get("Ping Channel", False),
        "Ping Here": fields.get("Ping Here", False),
        "Delete Messages": fields.get("Delete Messages", False),
        "Read Only": fields.get("Read Only", False)
    }


@app.command("/cm-hi")
def hello_command(ack, body, client):
    ack()
    client.chat_postMessage(
        channel=body["channel_id"],
        text=f"Hello, <@{body['user_id']}>!"
    )

@app.command("/cm-pingchannel")
def ping_channel_command(ack, body, client):
    ack()
    perms = get_perms(body["channel_id"], body["user_id"])
    # check if user is workspace admin or owner
    # if not, check if user has permission to ping channel
    print(perms)
    if perms.get("Ping Channel"):
        client.chat_postMessage(
            channel=body["channel_id"],
            text="Channel Ponged!"
        )
    else:
        client.chat_postMessage(
            channel=body["channel_id"],
            text="You do not have permission to ping this channel."
        )

@app.command("/cm-pinghere")
def ping_here_command(ack, body, client):
    ack()
    client.chat_postMessage(
        channel=body["channel_id"],
        text="Here Ponged!"
    )

@app.command("/cm-readonly")
def read_only_toggle(ack, body, client):
    ack()
    client.chat_postMessage(
        channel=body["channel_id"],
        text="Read-only mode toggled!"
    )

@app.command("/cm-manage")
def manage_command(ack, body, client):
    ack()
    client.chat_postMessage(
        channel=body["channel_id"],
        text="Manage command!"
    )

# Ready? Start your app!
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
