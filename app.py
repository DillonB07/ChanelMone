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

def is_workspace_admin(client, user_id):
    response = client.users_info(user=user_id)
    user = response.get("user")
    return user.get("is_admin") or user.get("is_owner") or user.get("is_primary_owner")


def is_channel_admin(client, channel_id, user_id):
    # slack doesn't provide a way to check for channel manager so we're just going to check if the user is the creator of the channel - this is normally the manager anyway
    response = client.conversations_info(channel=channel_id)
    channel = response.get("channel")
    creator = channel.get("creator")
    return creator == user_id


def get_perms(channel_id):
    perms = table.first(formula=f"{{Channel ID}} = '{channel_id}'")
    if not perms:
        perms = table.create({
            "Channel ID": channel_id
        })
    fields = perms.get("fields")

    return {
        "Ping Channel": fields.get("Ping Channel", False),
        "Ping Here": fields.get("Ping Here", False),
        "Delete Messages": fields.get("Delete Messages", False),
        "Read Only": fields.get("Read Only", False),
        "ID": perms.get("id")
    }


@app.command("/cm-pingchannel")
def ping_channel_command(ack, body, client):
    ack()
    is_admin = is_workspace_admin(client, body["user_id"])
    is_channel_manager = is_channel_admin(client, body["channel_id"], body["user_id"])

    if not is_admin and not is_channel_manager:
        client.chat_postMessage(
            channel=body["channel_id"],
            text="You do not have permission to ping this channel."
        )
        return
    perms = get_perms(body["channel_id"]) if not is_admin else {}

    if is_admin or (perms.get("Ping Channel") and is_channel_manager):
        client.chat_postMessage(
            channel=body["channel_id"],
            text="<!channel> Ponged!",
            link_names=1,
        )
    else:
        client.chat_postMessage(
            channel=body["channel_id"],
            text="You do not have permission to ping this channel."
        )


@app.command("/cm-pinghere")
def ping_here_command(ack, body, client):
    ack()

    is_admin = is_workspace_admin(client, body["user_id"])
    is_channel_manager = is_channel_admin(client, body["channel_id"], body["user_id"])
    
    if not is_admin and not is_channel_manager:
        client.chat_postMessage(
            channel=body["channel_id"],
            text="You do not have permission to ping this channel.",
        )
        return
    
    perms = get_perms(body["channel_id"]) if not is_admin else {}

    if is_admin or (perms.get("Ping Here") and is_channel_manager):
        client.chat_postMessage(
            channel=body["channel_id"],
            text="<!here> Ponged!",
            link_names=1,
        )
    else:
        client.chat_postMessage(
            channel=body["channel_id"],
            text="Please ask a member of <@fire-fighters> to authorise you to use this command."
        )


@app.command("/cm-readonly")
def read_only_toggle(ack, body, client):
    ack()

    is_admin = is_workspace_admin(client, body["user_id"])
    is_channel_manager = is_channel_admin(client, body["channel_id"], body["user_id"])

    if not is_admin and not is_channel_manager:
        client.chat_postMessage(
            channel=body["channel_id"],
            text="You do not have permission to toggle read only."
        )
        return
    
    perms = get_perms(body["channel_id"], body["user_id"]) 
    
    if not perms.get("Read Only"):
        table.update(perms['ID'], {"Read Only": True})
        client.chat_postMessage(
            channel=body["channel_id"],
            text="Channel is now read only."
        )
    else:
        table.update(perms["ID"], {"Read Only": False})
        client.chat_postMessage(
            channel=body["channel_id"],
            text="Channel is no longer read only."
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
