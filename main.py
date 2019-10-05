# Author: Caroline Forest
# Last updated: 4th Oct 2019

"""
TO DO

Minimum commands
- !lock
- !unlock
- !boss
"""


import discord
from config import (
    HELLO_TRIGGER, SOFTRESERVE_TRIGGER, LOCK_TRIGGER,
    SHOWTABLE_TRIGGER, BOSSLOOT_TRIGGER, HELP_TRIGGER
)
from settings import token, channel_name
from datetime import datetime


client = discord.Client()

PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item with spaces>", "UTC datetime"]


# def show_table(channel, item=None):
#     if item is None:
#         for key in PRIORITY_TABLE.keys():
#             channel.send("| {} | {} | {} | {} |".format(key, *PRIORITY_TABLE[key]))


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name == channel_name and message.content.startswith("!"):
        channel = message.channel
        if message.content.startswith(HELLO_TRIGGER):
            await channel.send("Greetings!")

        elif message.content.startswith(SOFTRESERVE_TRIGGER):
            # parse message for <name>/<class>/<item>
            info = message.content.replace(SOFTRESERVE_TRIGGER + " ", "").split("/")
            PRIORITY_TABLE[info[0]] = info[1:] + [datetime.utcnow()]
            await channel.send("You have your heart set on this item: [link].")

        elif message.content.startswith(LOCK_TRIGGER):
            # raise flag for no more soft reserves
            await channel.send("@Raider Raid priority is now locked!")

        elif message.content.startswith(SHOWTABLE_TRIGGER):
            # print table of reserves
            # prevent spam of table by limiting to once every minute or so?
            for key in PRIORITY_TABLE.keys():
                await channel.send("| {} | {} | {} | {} |".format(key, *PRIORITY_TABLE[key]))

        elif message.content.startswith(BOSSLOOT_TRIGGER):
            # print table for relevant reserved items in A-Z fashion
            pass

        elif message.content.startswith(HELP_TRIGGER):
            # PM possible commands
            await channel.send("Sliding into your DMs :wink:")
            pass

        else:
            await channel.send("No idea what you're saying, mate.")
            await channel.send("You having a stroke?")


try:
    client.run(token)
except RuntimeError:      # lol
    print("Exiting messily.")
except Exception as e:
    print(e)


"""
FEATURES

"""
