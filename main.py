# Author: Caroline Forest
# Last updated: 13th Oct 2019

"""
FIX
- message not popping up in sorting part of table builder

POTENTIAL EXCEPTIONS (to be dealt with)
- CommandNotFound (l 51)
- MissingRole (ll 148, 175, 184, 209, 222)

FEATURES
- manage channels
- status -> info of raid/number of people that reserved, also by role
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

deathcount per raid - timer based timeout
stricter enforcement on parsing
multiple channel separation
file history
loading previous raids
"""


import discord
import logging
from discord.ext.commands import Bot, has_role, CommandNotFound
from datetime import datetime
from io import BytesIO
from os import path

from utils import build_table, write_info, write_help

from loot_data import MC_BOSS_LOOT
from settings import (
    DISCORD_TOKEN, AUTHORIZED_CHANNELS, ADMIN_ROLE, PREFIX,
    MC_BOSS_NAMES, WOW_ROLES, WOW_CLASSES
)
from open_search.open_search import OpenSearch, OpenSearchError, SearchObjectError
from globals import GlobalState, Request
from decorators import save_state

logger = logging.getLogger(__name__)

bot = Bot(command_prefix=PREFIX)
bot.remove_command("help")


@bot.event
async def on_ready():
    logger.info("Successfully logged in as {}".format(bot.user.name))
    for channel in bot.get_all_channels():
        print(channel.name)


@bot.event
async def on_message(message):
    channel = message.channel
    if channel.type == discord.ChannelType.private:
        return
    elif channel.name in AUTHORIZED_CHANNELS:
        await bot.process_commands(message)


@bot.event
async def on_command_error(context, exception):
    if isinstance(exception, CommandNotFound):
        logger.warning("Unrecognized command: |{}|".format(context.message.content))
        await context.channel.send("I do not recognize that command.")
    else:
        logger.error(
            'Exception in command {}:'.format(context.command),
            exc_info=(type(exception), exception, exception.__traceback__)
        )


# BASIC COMMANDS
@bot.command()
async def hello(ctx):
    await ctx.send("Greetings!")


@bot.command()
async def info(ctx):
    embed = write_info()
    await ctx.send(embed=embed)


@bot.command()
@save_state
async def help(ctx):
    state = GlobalState()
    # get pleb and admin help messages
    embed_tuple = write_help()
    channel = ctx
    change = True

    if state.last_help is not None:
        delta = datetime.utcnow() - state.last_help

        # spam filter of 1 hour
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
        state.last_help = datetime.utcnow()

    await channel.send(embed=embed_tuple[0])
    await channel.send(embed=embed_tuple[1])


@bot.command()
@save_state
async def request(ctx, *message):
    state = GlobalState()
    # parse message for <name>/<class>/<item>
    # (one word for name and class right now)
    # and add/replace (if same name) to table
    if state.created is None:
        await ctx.send("There is no raid currently being tracked. Ask an officer to create one.")
        return

    if state.lock_flag:
        await ctx.send("Raid loot reservation is currently locked. Sorry!")
        return

    # cause it separate by space in message retrieval
    # cause it dumb.
    request = " ".join(list(message))
    if request.count("/") != 3:
        reply = "Um, maybe use **!help** first, love. It looks like you forgot something.:thinking:"
        await ctx.send(reply)
        return

    name, role, wow_class, item = [info.strip().casefold() for info in request.split("/")]
    if min(len(role), len(wow_class), len(item)) < 3:
        await ctx.send("Sorry but you must enter at least 3 letters to identify your role, class and item")
        return

    for existing_role in WOW_ROLES:
        if existing_role.startswith(role):
            role = existing_role
            break
    else:
        await ctx.send(
            (
                "Sorry, couldnt understand your declared role.\n"
                "Format is: `!request <name>/<role>/<class>/<item>`\n"
                "Your role choices are: {}"
            ).format(" | ".join(WOW_ROLES))
        )
        return

    for existing_class in WOW_CLASSES:
        if existing_class.startswith(wow_class):
            wow_class = existing_class
            break
    else:
        await ctx.send(
            (
                "Sorry, couldnt understand your declared class.\n"
                "Format is: `!request <name>/<role>/<class>/<item>`\n"
                "Your classes choices are: {}"
            ).format(" | ".join(WOW_CLASSES))
        )
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

    state.priority_table[name] = Request(
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
    except SearchObjectError:
        logger.exception("Failed to get tooltip data")
        await dm.send("Sorry! Something went wrong with the tooltip generation.")
    else:
        with BytesIO() as image_file:
            item.image.save(image_file, format="png")
            image_file.seek(0)
            await dm.send(file=discord.File(image_file, filename="reserved.png"))


@bot.command()
async def show(ctx, *message):
    state = GlobalState()
    # print table of requests in private message
    if state.priority_table != {}:
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
        table_list = build_table(state.priority_table, sort_by)
        for table in table_list:
            await dm_channel.send(table)

    else:
        await ctx.send("Nothing to show yet!")


# ADMIN COMMANDS
@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def newraid(ctx, *message):
    # initialize priority table and unlock soft reserves
    message = " ".join(message)
    GlobalState().newraid(info=message)
    await ctx.send("New raid loot reserves now open!")


@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def lock(ctx):
    # raise flag for no more soft reserves
    GlobalState().lock_flag = True
    await ctx.send("Raid priority is now locked!")


@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def unlock(ctx):
    # lower flag for more soft reserves
    GlobalState().lock_flag = False
    await ctx.send("Raid priority is open once more!")


@bot.command()
@has_role(ADMIN_ROLE)
async def showall(ctx, *message):
    # print table of requests in channel
    state = GlobalState()
    if state.priority_table != {}:
        sort_by = ""
        if message:
            sort_by = " ".join(message)
        table_list = build_table(state.priority_table, sort_by)
        for table in table_list:
            await ctx.send(table)
    else:
        await ctx.send("Nothing to show yet!")


@bot.command()
@has_role(ADMIN_ROLE)
async def boss(ctx, *message):
    # 1 or majordomo executus
    input = message
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
        input = " ".join(message)
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

    state = GlobalState()
    RELEVANT_TABLE = {}
    for item_num in potential_loot.keys():
        item_name = potential_loot[item_num]
        for character_name in state.priority_table.keys():
            if state.priority_table[character_name].item.casefold() == item_name.casefold():
                RELEVANT_TABLE[character_name] = state.priority_table[character_name]
    table_list = build_table(RELEVANT_TABLE)
    await ctx.send("**" + boss_name + "**")
    for table in table_list:
        await ctx.send(table)


@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def itemwin(ctx, character_name):
    state = GlobalState
    try:
        state.priority_table[character_name.casefold()].received_item = True
        await ctx.send("Congrats, {}!".format(character_name))
    except KeyError:
        await ctx.send("This name isn't in my list. :frowning:")


@bot.command()
@has_role(ADMIN_ROLE)
async def winners(ctx):
    state = GlobalState()
    if state.priority_table != {}:
        WINNERS = {}
        for player_name, request in state.priority_table.keys():
            if request.received_item:
                WINNERS[player_name] = state.priority_table[player_name]
        table_list = build_table(WINNERS, sort_by="name")
        for table in table_list:
            await ctx.send(table)


@bot.command()
async def status(ctx):
    pass

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
        filename="{}/lootbot.log".format(path.dirname(path.abspath(__file__))),
        level=logging.INFO,
        filemode='w',
        format="%(levelname)s:%(name)s:[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # logging.getLogger("discord").setLevel(logging.WARNING)
    # logging.getLogger("websockets").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.info(" ")
    logging.info("-" * 50)
    logging.info(" ")

    GlobalState().load_current_saved_state()

    try:
        bot.run(DISCORD_TOKEN)
    except RuntimeError:
        logger.info("Exiting messily.")
    except Exception as e:
        logger.info(e)
