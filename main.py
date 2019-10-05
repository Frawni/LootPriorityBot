# Author: Caroline Forest
# Last updated: 5th Oct 2019

"""
TO DO

Minimum commands
- !show --> prevent spam by checking time; better display
- !lock --> need to check for admin rights of some kind
- !unlock --> same
- !newraid --> same
- !help --> same
- !boss
"""


import discord
from discord.ext.commands import Bot
from datetime import datetime

from config import AUTHORIZED_CHANNELS
from settings import token

bot = Bot(command_prefix='!')

PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item with spaces>", "UTC datetime"]
lock_flag = 0


@bot.event
async def on_ready():
    print("We have logged in as {}".format(bot.user.name))


@bot.event
async def on_message(message):
    channel = message.channel
    if channel.name in AUTHORIZED_CHANNELS:
        await bot.process_commands(message)
    elif channel.type == discord.ChannelType.private:
        await channel.send("Whatever you say, darling.")


@bot.command()
async def hello(ctx):
    await ctx.send("Greetings!")


@bot.command()
async def newraid(ctx):
    # initialize priority table and unlock soft reserves
    PRIORITY_TABLE = {}
    lock_flag = 0
    await channel.send("Raid priority is now open!")


@bot.command()
async def request(ctx):
    # parse message for <name>/<class>/<item>
    # and add/replace (if same name) to table
    if not lock_flag:
        info = message.content.split("/")
        PRIORITY_TABLE[info[0]] = info[1:] + [datetime.utcnow()]
        reply = "You have your heart set on this item: [link]."
    else:
        reply = "Raid priority is locked. Sorry!"
    await ctx.send(reply)


@bot.command()
async def lock(ctx):
    # raise flag for no more soft reserves
    lock_flag = 1
    await ctx.send("Raid priority is now locked!")


@bot.command()
async def unlock(ctx):
    # lower flag for more soft reserves
    lock_flag = 0
    await ctx.send("Raid priority is open once more!")


@bot.command()
async def newraid(ctx):
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
        user = message.author
        dm_channel = user.dm_channel
        if dm_channel is None:
            await user.create_dm()
            dm_channel = user.dm_channel
        await channel.send("Sliding into your DMs :wink:")
        await dm_channel.send(HELP_MESSAGE_PLEB)

    else:
        await channel.send("No idea what you're saying, mate.")
        await channel.send("You having a stroke?")


try:
    bot.run(token)
except RuntimeError:
    print("Exiting messily.")
except Exception as e:
    print(e)


"""
FEATURES
oh the possibilities
"""
