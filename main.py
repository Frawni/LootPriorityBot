# Author: Caroline Forest
# Last updated: 6th Oct 2019

"""
BARE MINIMUM
- !boss

POTENTIAL EXCEPTIONS (to be dealt with)
- CommandNotFound (l 51)
- MissingRole (ll 148, 175, 184, 209, 222)
"""


import discord
from discord.ext.commands import Bot, has_role
from datetime import datetime

from functions import build_table_str, write_info, write_help

from config import AUTHORIZED_CHANNELS, ADMIN_ROLE, PREFIX
from settings import token


# GLOBAL VARIABLES
bot = Bot(command_prefix=PREFIX)
bot.remove_command("help")

PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item>", "UTC datetime"]
lock_flag = True         # bool (true when locked, false when unlocked)

# Prevent spam --> PM if less than an hour in channel
last_help = None   # last help message sent in channel


@bot.event
async def on_ready():
    print("Successfully logged in as {}".format(bot.user.name))


@bot.event
async def on_message(message):
    channel = message.channel
    if channel.type == discord.ChannelType.private:
        return
    elif channel.name in AUTHORIZED_CHANNELS:
        await bot.process_commands(message)      # maybe deal with CommandNotFound? but so far doesn't break, just prints in terminal


@bot.command()
async def hello(ctx):
    await ctx.send("Greetings!")


@bot.command()
async def info(ctx):
    embed = write_info()
    await ctx.send(embed=embed)


@bot.command()
async def help(ctx):
    # spam filter of 1 hour
    global last_help

    # get pleb and admin help messages
    embed_tuple = write_help()
    channel = ctx
    change = True

    if last_help is not None:
        delta = datetime.utcnow() - last_help

        if delta.days == 0 and delta.seconds < 3600:
            # get user private message channel, or create if doesn't exist
            user = ctx.author
            dm_channel = user.dm_channel
            if dm_channel is None:
                await user.create_dm()
                dm_channel = user.dm_channel

            channel = dm_channel
            change = False
            await ctx.send("Sliding into your DMs, we don't want to spam, now. :wink:")

    if change:
        last_help = datetime.utcnow()

    await channel.send(embed=embed_tuple[0])
    await channel.send(embed=embed_tuple[1])


@bot.command()
@has_role(ADMIN_ROLE)
async def newraid(ctx):
    # initialize priority table and unlock soft reserves
    global PRIORITY_TABLE, lock_flag
    PRIORITY_TABLE = {}
    lock_flag = False
    await ctx.send("Raid priority is now open!")


@bot.command()
async def request(ctx, *args):
    # parse message for <name>/<class>/<item>
    # (one word for name and class right now)
    # and add/replace (if same name) to table
    if not lock_flag:
        # cause it separate by space in message retrieval
        # cause it dumb.
        request = " ".join(list(args))

        if request.count("/") == 2:
            info = request.split("/")
            PRIORITY_TABLE[info[0]] = info[1:] + [datetime.utcnow(), ]
            reply = "Noted!"

        else:
            reply = "Um, maybe use !help first, love. It looks like you made too many or too little requests.:thinking:"

    else:
        reply = "Raid priority is locked. Sorry!"

    await ctx.send(reply)


@bot.command()
@has_role(ADMIN_ROLE)
async def lock(ctx):
    # raise flag for no more soft reserves
    global lock_flag
    lock_flag = True
    await ctx.send("Raid priority is now locked!")


@bot.command()
@has_role(ADMIN_ROLE)
async def unlock(ctx):
    # lower flag for more soft reserves
    global lock_flag
    lock_flag = False
    await ctx.send("Raid priority is open once more!")


@bot.command()
async def show(ctx):
    # print table of requests in private message
    if PRIORITY_TABLE != {}:
        table = build_table_str(PRIORITY_TABLE, ["Name", "Class", "Item Requested", "Time of Request (UTC)"])

        # get user private message channel, or create if doesn't exist
        user = ctx.author
        dm_channel = user.dm_channel
        if dm_channel is None:
            await user.create_dm()
            dm_channel = user.dm_channel

        await ctx.send("Sliding into your DMs :wink:")
        await dm_channel.send(table)

    else:
        await ctx.send("Nothing to show yet!")


@bot.command()
@has_role(ADMIN_ROLE)
async def showall(ctx):
    # print table of requests in channel
    if PRIORITY_TABLE != {}:
        table = build_table_str(PRIORITY_TABLE, ["Name", "Class", "Item Requested", "Time of Request (UTC)"])
        await ctx.send(table)

    else:
        await ctx.send("Nothing to show yet!")


@bot.command()
@has_role(ADMIN_ROLE)
async def boss(ctx):
    pass


try:
    bot.run(token)

except RuntimeError:
    print("Exiting messily.")

except Exception as e:
    print(e)
