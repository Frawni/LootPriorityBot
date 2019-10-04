# Author: Caroline Forest
# Last updated: 4th Oct 2019

"""
TO DO

Minimum commands
- !soft
- !show
- !lock
- !boss
"""


import discord
from config import (
    HELLO_TRIGGER, SOFTRESERVE_TRIGGER, LOCK_TRIGGER,
    SHOWTABLE_TRIGGER, BOSSLOOT_TRIGGER, HELP_TRIGGER
)
from settings import token


client = discord.Client()


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!"):
        if message.content.startswith(HELLO_TRIGGER):
            await message.channel.send("Greetings!")

        elif message.content.startswith(SOFTRESERVE_TRIGGER):
            # parse message for <name>/<class>/<item>
            await message.channel.send("Noted!")

        elif message.content.startswith(LOCK_TRIGGER):
            # raise flag for no more soft reserves
            await message.channel.send("@Raider Raid priority is now locked")

        elif message.content.startswith(SHOWTABLE_TRIGGER):
            # print table of reserves
            # prevent spam of table by limiting to once every minute or so?
            pass

        elif message.content.startswith(BOSSLOOT_TRIGGER):
            # print table for relevant reserved items in A-Z fashion
            pass

        elif message.content.startswith(HELP_TRIGGER):
            # PM possible commands
            await message.channel.send("Sliding into your DMs :wink:")
            pass

        else:
            await message.channel.send("No idea what you're saying, mate.")
            await message.channel.send("You having a stroke?")


try:
    client.run(token)
except RuntimeError:      # lol
    print("Exiting messily.")
except Exception as e:
    print(e)


"""
FEATURES
- figure out how to live in only a set on invite specific channel
"""
