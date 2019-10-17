# Author: Caroline Forest
# Last updated: 13th Oct 2019

"""
FIX
- message not popping up in sorting part of table builder

POTENTIAL EXCEPTIONS (to be dealt with)
- CommandNotFound (l 51)
- MissingRole (ll 148, 175, 184, 209, 222)

FEATURES
- set admin role on bot invite (+ allow more than one role?)
- deal with second channel, different commands
- search function for tooltip/through table
- add boss name when receiving loot
- identify who hasn't made a request yet/count number of people requesting/items requested
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
import logging
from discord.ext.commands import Bot, has_role
from datetime import datetime
from recordclass import recordclass
from functools import wraps

from functions import build_table, write_info, write_help, json_dump, json_load

from loot_data import MC_BOSS_LOOT
from config import AUTHORIZED_CHANNELS, ADMIN_ROLE, PREFIX, MC_BOSS_NAMES
from settings import token, SAVE_FILEPATH, PREVIOUS_SAVE_FILEPATH
from open_search.open_search import OpenSearch, OpenSearchError, SearchObjectError

logger = logging.getLogger(__name__)
# GLOBAL VARIABLES
bot = Bot(command_prefix=PREFIX)
bot.remove_command("help")

PRIORITY_TABLE = {}      # "<name>": Request recordclass
Request = recordclass("Request", ["role", "wow_class", "item", "datetime", "received_item"])
lock_flag = True        # bool (true when locked, false when unlocked)

# Prevent spam --> PM if less than an hour in channel
last_help = None   # last help message sent in channel


def save_state(func):
    """
    Decorator to dump the contents of PRIORITY_TABLE after every modifications
    """
    @wraps(func)
    async def decorated(*args, **kwargs):
        await func(*args, **kwargs)
        to_save = [PRIORITY_TABLE, lock_flag]
        with open(SAVE_FILEPATH, "w") as f:
            json_dump(to_save, f)
    return decorated


@bot.event
async def on_ready():
    logger.info("Successfully logged in as {}".format(bot.user.name))


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
@save_state
async def request(ctx, *args):
    # parse message for <name>/<class>/<item>
    # (one word for name and class right now)
    # and add/replace (if same name) to table
    if lock_flag:
        reply = "Raid priority is locked. Sorry!"
        await ctx.send(reply)
        return

    # cause it separate by space in message retrieval
    # cause it dumb.
    request = " ".join(list(args))
    name, role, wow_class, item = [info.strip().casefold() for info in request.split("/")]
    if request.count("/") != 3:
        reply = "Um, maybe use **!help** first, love. It looks like you forgot something.:thinking:"
        await ctx.send(reply)
        return

    try:
        search = OpenSearch('item', item)
    except OpenSearchError as e:
        logger.info(e)
        await ctx.send("Could not find any matching items. Try again.")
        return

    # Valid item is one that we found on WoWhead and that is also part of our loot table
    valid_item = None
    for item in search.results:
        for boss in MC_BOSS_LOOT:
            if item.id in MC_BOSS_LOOT[boss]:
                valid_item = item
                break
        else:
            # If we didnt break out of inner loop, continue with outer
            continue
        # If we did break out of inner loop, break out of the outer too
        break

    if valid_item is None:
        await ctx.send("Found some items but none matched the droptable from bosses for this raid. Try again.")
        return

    PRIORITY_TABLE[name] = Request(
        role=role, wow_class=wow_class, item=item.name,
        datetime=datetime.utcnow(), received_item=False
    )
    user = ctx.author
    await ctx.send(
        (
            "Confirmed! Noting down [{}] for {}. "
            "Check your DMs for the item's tooltip just to be sure!"
        ).format(item.name, name.title())
    )

    dm = user.dm_channel
    if dm is None:
        await user.create_dm()
        dm = user.dm_channel

    try:
        item.get_tooltip_data()
    except SearchObjectError as e:
        logger.info(e)
        await dm.send("Sorry! Something went wrong with the tooltip generation.")
    else:
        await dm.send(file=discord.File(item.image))
        os.remove(item.image)


@bot.command()
async def show(ctx, *message):
    # print table of requests in private message
    if PRIORITY_TABLE != {}:
        # get user private message channel, or create if doesn't exist
        user = ctx.author
        dm_channel = user.dm_channel
        if dm_channel is None:
            await user.create_dm()
            dm_channel = user.dm_channel

        await ctx.send("Sliding into your DMs :wink:")

        sort_by = ""
        if message:
            sort_by = " ".join(message)
        table_list = build_table(PRIORITY_TABLE, sort_by)
        for table in table_list:
            await dm_channel.send(table)

    else:
        await ctx.send("Nothing to show yet!")


# ADMIN COMMANDS
@bot.command()
@has_role(ADMIN_ROLE)
async def newraid(ctx):
    global PRIORITY_TABLE, lock_flag

    to_save = [PRIORITY_TABLE, lock_flag]
    with open(PREVIOUS_SAVE_FILEPATH, "w") as f:
        json_dump(to_save, f)
    try:
        os.remove(SAVE_FILEPATH)
    except FileNotFoundError:
        pass

    # initialize priority table and unlock soft reserves
    PRIORITY_TABLE = {}
    lock_flag = False
    await ctx.send("Raid priority is now open!")


@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def lock(ctx):
    # raise flag for no more soft reserves
    global lock_flag
    lock_flag = True
    await ctx.send("Raid priority is now locked!")


@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def unlock(ctx):
    # lower flag for more soft reserves
    global lock_flag
    lock_flag = False
    await ctx.send("Raid priority is open once more!")


@bot.command()
@has_role(ADMIN_ROLE)
async def showall(ctx, *message):
    # print table of requests in channel
    if PRIORITY_TABLE != {}:
        sort_by = ""
        if message:
            sort_by = " ".join(message)
        table_list = build_table(PRIORITY_TABLE, sort_by)
        for table in table_list:
            await ctx.send(table)
    else:
        await ctx.send("Nothing to show yet!")


@bot.command()
@has_role(ADMIN_ROLE)
async def boss(ctx, *args):
    # 1 or majordomo executus
    input = args
    if not len(input):
        await ctx.send("Wtf mate gimme somen to work with here")
        return

    potential_loot = None
    boss_name = None
    if input[0].isdigit():
        # Boss identified by his number
        boss_number = int(input[0]) - 1
        if boss_number not in range(len(MC_BOSS_NAMES)):
            await ctx.send("Not a real number.")
            return
        else:
            boss_name = MC_BOSS_NAMES[boss_number]
            potential_loot = MC_BOSS_LOOT[boss_name]
    else:
        # Boss identified by name
        input = " ".join(args)
        for name in MC_BOSS_NAMES:
            if input.casefold() in name:
                boss_name = name
                potential_loot = MC_BOSS_LOOT[boss_name]
                break
        else:
            await ctx.send("No boss with that name found")
            return

    assert boss_name is not None
    assert potential_loot is not None

    RELEVANT_TABLE = {}
    for item_num in potential_loot.keys():
        item_name = potential_loot[item_num]
        for character_name in PRIORITY_TABLE.keys():
            if PRIORITY_TABLE[character_name].item.casefold() == item_name.casefold():
                RELEVANT_TABLE[character_name] = PRIORITY_TABLE[character_name]
    table_list = build_table(RELEVANT_TABLE)
    await ctx.send("**" + boss_name + "**")
    for table in table_list:
        await ctx.send(table)


@bot.command()
@has_role(ADMIN_ROLE)
@save_state
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
        table_list = build_table(WINNERS, sort_by="name")
        for table in table_list:
            await ctx.send(table)


# # QUICK AND DIRTY AUTOMATION OF TEXT CAUSE I CAN'T SEEM TO BE ABLE TO READ OTHER BOT MESSAGES
# @bot.command()
# async def doit(ctx):
#     with open("requests.txt", "r") as f:
#         for line in f:
#             name, role, wow_class, item = [info.strip().casefold() for info in line.split("/")]
#             try:
#                 search = OpenSearch('item', item)
#             except OpenSearchError as e:
#                 logger.info(e)
#                 await ctx.send("Could not find any matching items. Try again.")
#                 return
#
#             # valid_item = None
#             for item in search.results:
#                 for boss in MC_BOSS_LOOT:
#                     if item.id in MC_BOSS_LOOT[boss]:
#                         # valid_item = item
#                         break
#                 else:
#                     continue
#                 break
#
#             # if valid_item is None:
#             #     await ctx.send("Found some items but none matched the droptable from bosses for this raid. Try again.")
#             #     return
#
#             PRIORITY_TABLE[name] = Request(
#                 role=role, wow_class=wow_class, item=item.name,
#                 datetime=datetime.utcnow(), received_item=False
#             )
#     table_list = build_table(PRIORITY_TABLE)
#     for table in table_list:
#         await ctx.send(table)

if __name__ == "__main__":
    logging.basicConfig(
        filename="{}/lootbot.log".format(os.path.dirname(os.path.abspath(__file__))),
        level=logging.DEBUG,
        filemode='a',
        format="%(levelname)s:%(name)s:[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info(" ")
    logging.info("-" * 50)
    logging.info(" ")
    try:
        with open(SAVE_FILEPATH, "r") as f:
            previous_table, previous_lock_flag = json_load(f)
            PRIORITY_TABLE = {k: Request(**v) for k, v in previous_table.items()}
            lock_flag = previous_lock_flag
    except FileNotFoundError:
        logger.info("No previous save file found")

    try:
        bot.run(token)
    except RuntimeError:
        logger.info("Exiting messily.")
    except Exception as e:
        logger.info(e)
