# Author: Caroline Forest
# Last updated: 8th Oct 2019

"""
BARE MINIMUM
- !winners --> need to add mob name to table

POTENTIAL EXCEPTIONS (to be dealt with)
- CommandNotFound (l 51)
- MissingRole (ll 148, 175, 184, 209, 222)

FEATURES
- set admin role on bot invite (+ allow more than one role?)
- deal with second channel, different commands
- sort by class
- sort by role
- search function for tooltip/through table
- !spreadsheet --> use google sheets api to have a shareable link
- keep record of previous raids, and have appropriate commands for such
- pretty stats based on previous raids?
- !setraid --> for when more raids are accesible, and also if only certain bosses are killed
- !count --> return number of people that have made a request
- !roll --> cause deep down, I'm a troll
- wow add-on to remove going through discord when raiding (MEGA feature, obviously)
"""


import discord
import os
from discord.ext.commands import Bot, has_role
from datetime import datetime
from recordclass import recordclass

from functions import build_table_str, write_info, write_help

from loot_data import MC_BOSS_LOOT
from config import AUTHORIZED_CHANNELS, ADMIN_ROLE, PREFIX
from settings import token


# GLOBAL VARIABLES
bot = Bot(command_prefix=PREFIX)
bot.remove_command("help")

PRIORITY_TABLE = {}      # "<name>": Request recordclass
Request = recordclass("Request", ["role", "wow_class", "item", "datetime", "received_item"])
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


# BASIC COMMANDS
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
            await ctx.send("Sliding into your DMs, we don't want to spam, now. :kissing_heart:")

    if change:
        last_help = datetime.utcnow()

    await channel.send(embed=embed_tuple[0])
    await channel.send(embed=embed_tuple[1])


@bot.command()
async def request(ctx, *args):
    # parse message for <name>/<class>/<item>
    # (one word for name and class right now)
    # and add/replace (if same name) to table
    if not lock_flag:
        # cause it separate by space in message retrieval
        # cause it dumb.
        request = " ".join(list(args))

        if request.count("/") == 3:
            name, role, wow_class, item = [info.strip().casefold() for info in request.split("/")]
            PRIORITY_TABLE[name] = Request(role=role, wow_class=wow_class, item=item,
                                           datetime=datetime.utcnow(), received_item=False)
            reply = "Noted!"

        else:
            reply = "Um, maybe use **!help** first, love. It looks like you made too many or too little requests.:thinking:"

    else:
        reply = "Raid priority is locked. Sorry!"

    await ctx.send(reply)


@bot.command()
async def show(ctx):
    # print table of requests in private message
    if PRIORITY_TABLE != {}:
        table = build_table_str(PRIORITY_TABLE)

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


# ADMIN COMMANDS
@bot.command()
@has_role(ADMIN_ROLE)
async def newraid(ctx):
    # initialize priority table and unlock soft reserves
    global PRIORITY_TABLE, lock_flag
    PRIORITY_TABLE = {}
    lock_flag = False
    await ctx.send("Raid priority is now open!")


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
@has_role(ADMIN_ROLE)
async def showall(ctx):
    # print table of requests in channel
    if PRIORITY_TABLE != {}:
        table = build_table_str(PRIORITY_TABLE)
        await ctx.send(table)

    else:
        await ctx.send("Nothing to show yet!")


@bot.command()
@has_role(ADMIN_ROLE)
async def boss(ctx, boss_name):
    try:
        POTENTIAL_LOOT = MC_BOSS_LOOT[boss_name.casefold()]
        RELEVANT_TABLE = {}
        for item_num in POTENTIAL_LOOT.keys():
            item_name = POTENTIAL_LOOT[item_num]
            for character_name in PRIORITY_TABLE.keys():
                if PRIORITY_TABLE[character_name].item.casefold() == item_name.casefold():
                    RELEVANT_TABLE[character_name] = PRIORITY_TABLE[character_name]
        message = build_table_str(RELEVANT_TABLE)
    except KeyError:
        message = "I don't know this boss, sorry!"
    await ctx.send(message)


@bot.command()
@has_role(ADMIN_ROLE)
async def itemwin(ctx, character_name):
    try:
        PRIORITY_TABLE[character_name.casefold()].received_item = True
        await ctx.send("Congrats, {}!".format(character_name))
    except KeyError:
        await ctx.send("This name isn't in my list. :frowning:")


@bot.command()
@has_role(ADMIN_ROLE)
async def winners(ctx):
    if PRIORITY_TABLE != {}:
        WINNERS = {}
        for key in PRIORITY_TABLE.keys():
            if PRIORITY_TABLE[key].received_item:
                WINNERS[key] = PRIORITY_TABLE[key]
        table = build_table_str(WINNERS)
        await ctx.send(table)


try:
    bot.run(token)

except RuntimeError:
    print("Exiting messily.")
except Exception as e:
    print(e)
