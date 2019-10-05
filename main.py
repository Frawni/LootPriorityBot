# Author: Caroline Forest
# Last updated: 5th Oct 2019

"""
TO DO

Minimum commands
- !show --> prevent spam by checking time
- !lock --> need to check for admin rights of some kind
- !unlock --> same
- !newraid --> same
- !boss
- !help
"""


import discord
from config import (
    NEWRAID_TRIGGER, HELLO_TRIGGER, SOFTRESERVE_TRIGGER, LOCK_TRIGGER,
    UNLOCK_TRIGGER, SHOWTABLE_TRIGGER, BOSSLOOT_TRIGGER, HELP_TRIGGER
)
from settings import token, channel_name
from datetime import datetime


client = discord.Client()

PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item with spaces>", "UTC datetime"]
lock_flag = 0

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
        global lock_flag
        global PRIORITY_TABLE
        channel = message.channel

        if message.content.startswith(HELLO_TRIGGER):
            await channel.send("Greetings!")

        elif message.content.startswith(NEWRAID_TRIGGER):
            # initialize priority table and unlock soft reserves
            PRIORITY_TABLE = {}
            lock_flag = 0
            await channel.send("@Raider Raid priority is now open!")

        elif message.content.startswith(SOFTRESERVE_TRIGGER):
            # parse message for <name>/<class>/<item>
            # and add/replace (if same name) to table
            if not lock_flag:
                info = message.content.replace(SOFTRESERVE_TRIGGER + " ", "").split("/")
                PRIORITY_TABLE[info[0]] = info[1:] + [datetime.utcnow()]
                reply = "@Frawni You have your heart set on this item: [link]."
            else:
                reply = "Raid priority is locked. Sorry!"
            await channel.send(reply)

        elif message.content.startswith(LOCK_TRIGGER):
            # raise flag for no more soft reserves
            lock_flag = 1
            await channel.send("@Raider Raid priority is now locked!")

        elif message.content.startswith(UNLOCK_TRIGGER):
            # lower flag for more soft reserves
            lock_flag = 0
            await channel.send("@Raider Raid priority is open once more!")

        elif message.content.startswith(SHOWTABLE_TRIGGER):
            # print table of reserves
            # prevent spam of table by limiting to once every minute or so?
            await channel.send("| Name | Class | Item Requested | Time of Request |")
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
