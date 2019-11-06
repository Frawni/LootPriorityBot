# Last updated: 26th Oct 2019

"""
TODO
- End raid command
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

deathcount per raid - timer based timeout
stricter enforcement on parsing
multiple channel separation
file history
loading previous raids
"""


import discord
import logging
import asyncio
from discord.ext.commands import Bot, has_role, CommandNotFound, MissingRole
from datetime import datetime
from io import BytesIO
from os import path
from json import JSONDecodeError

from utils import (
    write_info, write_help, init_update_messages,
    update_status, update_table, build_update_table
)

from loot_data import MC_BOSS_LOOT
from settings import (
    DISCORD_TOKEN, AUTHORIZED_CHANNELS, ADMIN_ROLE, PREFIX, NEW_RAID_SPLIT_TOKEN, NEW_RAID_CANCEL_TRIGGER,
    INFO_CHANNEL_NAME, REQUEST_CHANNEL_NAME, NUM_MESSAGES_FOR_TABLE,
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
    logger.info(f"Successfully logged in as {bot.user.name}")

    logger.info("Looking for info channel")
    info_channel = None
    for channel in bot.get_all_channels():
        if channel.name == INFO_CHANNEL_NAME:
            info_channel = channel
            break

    if info_channel is None:
        logger.error(f"Could not find info channel, options were: {bot.get_all_channels()} ")
        exit()

    state = GlobalState()
    state.info_channel = channel
    # Loading/Initializing references to the auto-updating messages
    logger.info("Initializing updating messages")
    logger.info(f"Status_message is: |{state.status_message}|\nTable_message is: |{state.table_messages}|")
    if state.status_message is None or len(state.table_messages) != NUM_MESSAGES_FOR_TABLE:
        await init_update_messages(channel)
    else:
        try:
            state.status_message = await channel.fetch_message(state.status_message)
            for i in range(NUM_MESSAGES_FOR_TABLE):
                state.table_messages[i] = await channel.fetch_message(state.table_messages[i])
        except discord.NotFound:
            logger.warning("Could not find info/status messages by their saved id. Reiniting")
            await init_update_messages(channel)

    await update_status()
    await update_table()
    state.initialized = True
    state.save_current_state()


@bot.event
async def on_message(message):
    # Ignore messages that we sent
    if message.author.id == bot.user.id:
        return

    state = GlobalState()
    while not state.initialized:
        await asyncio.sleep(1)

    channel = message.channel
    # New raid is being set up
    if channel.type == discord.ChannelType.private:
        if state.new_raid_user_id == message.author.id:
            await process_new_raid(message)

    # We only care for our 3 channels, rest can be ignored
    elif channel.name in AUTHORIZED_CHANNELS:
        # Only request commands are allowed in the request channel
        if channel.name == REQUEST_CHANNEL_NAME:
            if message.content.startswith(f"{PREFIX}request"):
                await bot.process_commands(message)
            else:
                await message.delete()
                user = message.author
                user_dm = user.dm_channel
                if user_dm is None:
                    await user.create_dm()
                    user_dm = user.dm_channel
                await user_dm.send(
                    f"Only requests allowed in the `{REQUEST_CHANNEL_NAME}` channel"
                )
        else:
            await bot.process_commands(message)


async def process_new_raid(message):
    state = GlobalState()
    user_dm = message.channel
    raid_info = message.content

    if raid_info.strip().lower() == "cancel":
        state.new_raid_user_id = None
        await user_dm.send("Cancelling new raid. No changes have been made.")
        return

    if message.content.count(NEW_RAID_SPLIT_TOKEN) != 3:
        await user_dm.send(
            f"Not enough information supplied. You need to give 4 things split by 3 {NEW_RAID_SPLIT_TOKEN}"
        )
        return

    raid_name, raid_desc, raid_date, raid_time = [
        info.strip()
        for info in message.content.split(NEW_RAID_SPLIT_TOKEN)
    ]
    if raid_time.count(":") != 1 or raid_date.count("/") != 2:
        await user_dm.send(
            "Your date and/or time is not formatted properly. Are you sure you are using '/' and ':'?"
        )
        return

    # Make sure both inputs are 0-padded digits for the datetime parser
    raid_date = "/".join(
        [
            part.strip().rjust(2, "0")                   # All digits must be 2 chars for datetime parse
            if idx != 2 else part.strip().rjust(4, "0")  # Year needs to be padded to 4
            for idx, part in enumerate(raid_date.split("/"))
        ]
    )
    raid_time = ":".join([part.strip().rjust(2, "0") for part in raid_time.split(":")])
    try:
        raid_datetime = datetime.strptime(f"{raid_date} {raid_time}", "%d/%m/%Y %H:%M")
    except ValueError as e:
        print(e)
        await user_dm.send(
            "Your date and/or time is completely fucked. What did you do?"
        )
        return
    await user_dm.send("All good! Initializing new raid.")
    state.new_raid(
        name=raid_name.strip(),
        description=raid_desc.strip(),
        when=raid_datetime
    )
    await user_dm.send("Saving new state.")
    state.save_current_state()
    await user_dm.send(f"Wiping `{INFO_CHANNEL_NAME}` channel.")
    bots_messages = [msg.id for msg in state.table_messages] + [state.status_message.id]
    async for message in state.info_channel.history(limit=None):
        if message.id not in bots_messages:
            await message.delete()

    await user_dm.send(f"Updating banners in the `{INFO_CHANNEL_NAME}` channel.")
    await update_table()
    await update_status()
    await user_dm.send(f"Announcing new raid in `{REQUEST_CHANNEL_NAME}` channel.")

    logger.info("Looking for request channel for new raid announcement")
    request_channel = None
    for channel in bot.get_all_channels():
        if channel.name == REQUEST_CHANNEL_NAME:
            request_channel = channel
            break
    if request_channel:
        await user_dm.send("Could not find the request channel so continuing with no announcement.")
    else:
        await request_channel.send("New raid is now live!")

    await user_dm.send("New raid ready to go!")


@bot.event
async def on_command_error(context, exception):
    if isinstance(exception, CommandNotFound):
        logger.warning(f"Unrecognized command: |{context.message.content}|")
        await context.channel.send("I do not recognize that command. Learn to type. Or read. Or both.")
    elif isinstance(exception, MissingRole):
        logger.warning(f"Missing role for user: |{context.message.author}| for message: |{context.message.content}")
        await context.channel.send("You do not have the permissions to use that command. Newb.")
    else:
        logger.error(
            f"Exception in command |{context.command}|. On message |{context.message.content}|. From user |{context.message.author.display_name}|",
            exc_info=(type(exception), exception, exception.__traceback__)
        )


# BASIC COMMANDS
@bot.command()
async def hello(ctx):
    await ctx.send("Hewo! UwU")


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
        delta = datetime.now() - state.last_help

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
            await ctx.send("Sliding into your DMs to give you some _personal_ help. :kissing_heart:")

    if change:
        state.last_help = datetime.now()

    await channel.send(embed=embed_tuple[0])
    await channel.send(embed=embed_tuple[1])


@bot.command(rest_is_raw=True)
@save_state
async def request(ctx, *, request):
    request = request.strip()
    if ctx.channel.name != REQUEST_CHANNEL_NAME:
        await ctx.send(f"Requests can only be done in the `{REQUEST_CHANNEL_NAME}` channel. Now begone.")
        return

    state = GlobalState()
    if state.created is None:
        await ctx.send(f"There is no raid currently being tracked. Complain to an {ADMIN_ROLE} until something happens.")
        return

    if state.lock_flag:
        await ctx.send("Raid loot reservation is currently locked.")
        return

    user = ctx.author
    user_dm = user.dm_channel
    user_message = ctx.message
    if user_dm is None:
        await user.create_dm()
        user_dm = user.dm_channel

    if request.count("/") != 3:
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: / count"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "It looks like you forgot something.:thinking:\n"
                f"Fix your command (and your life) and message me again in the `{REQUEST_CHANNEL_NAME}` channel!\n"
            )
        )
        await user_message.delete()
        return

    name, role, wow_class, item = [info.strip().casefold() for info in request.split("/")]
    if min(len(role), len(wow_class), len(item), len(name)) < 3:
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: len check"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "I don't speak whatever this is. Write things out properly - and spell them right ffs.\n"
                f"Fix your command (and your life) and message me again in the `{REQUEST_CHANNEL_NAME}` channel!"
            )
        )
        await user_message.delete()
        return

    for existing_role in WOW_ROLES:
        if existing_role.startswith(role):
            role = existing_role
            break
    else:
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: role check"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "Couldn't understand your declared role.\n"
                "Format is: `>request <name>/<role>/<class>/<item>`\n"
                f"Your role choices are: {' | '.join(WOW_ROLES)}\n"
                f"Fix your command (and your life) and message me again in the `{REQUEST_CHANNEL_NAME}` channel!"
            )
        )
        await user_message.delete()
        return

    for existing_class in WOW_CLASSES:
        if existing_class.startswith(wow_class):
            wow_class = existing_class
            break
    else:
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: class check"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "Couldn't understand your declared class.\n"
                "Format is: `>request <name>/<role>/<class>/<item>`\n"
                f"Your classes choices are: {' | '.join(WOW_CLASSES)}\n"
                f"Fix your command (and your life) and message me again in the `{REQUEST_CHANNEL_NAME}` channel!"
            )
        )
        await user_message.delete()
        return

    try:
        search = OpenSearch('item', item)
    except OpenSearchError as e:
        logger.warning(e)
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: item exists check"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "Could not find any matching items.\n"
                f"Figure your shit out and message me again in the `{REQUEST_CHANNEL_NAME}` channel!"
            )
        )
        await user_message.delete()
        return
    except JSONDecodeError:
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: wowhead is being a dick"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "Could not properly fetch data from wowhead.\n"
                "Wowhead is probably just feeling like being a dick at the moment - try the request again in a little while.\n"
                "If problems continue then give Frawni or Malzo a poke!"
            )
        )
        await user_message.delete()
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
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: valid item check"
            )
        )
        await user_dm.send(
            (
                f"You sent: `{user_message.content}`\n\n"
                "Look, I agree, that is an item. You also have _zero_ chance of getting it doing this raid.\n"
                f"Figure your shit out and message me again in the `{REQUEST_CHANNEL_NAME}` channel!"
            )
        )
        await user_message.delete()
        return

    request = Request(
        role=role, wow_class=wow_class, item=item.name,
        datetime=datetime.now(), received_item=False
    )
    state.priority_table[name] = request
    request = request.as_presentable()
    await ctx.send(
        (
            f"Noting down [{item.name}] for {name.title()}.\n"
            f"Class: {request.wow_class} \t Role: {request.role}\n"
        )
    )

    try:
        item.get_tooltip_data()
    except SearchObjectError:
        logger.warning(
            (
                f"Failed loot request from |{user_message.author.display_name}|. "
                f"Messaged: |{user_message.content}|. "
                "Reason: tooltip broke"
            )
        )
        logger.exception("Failed to get tooltip data")
        await user_dm.send("Well, the tooltip generation fucked up. There's a limit to how much I can fix someone else's code.")
    else:
        with BytesIO() as image_file:
            item.image.save(image_file, format="png")
            image_file.seek(0)
            await user_dm.send(file=discord.File(image_file, filename="reserved.png"))


@bot.command(rest_is_raw=True)
async def show(ctx, *, sort_by):
    sort_by = sort_by.strip()

    state = GlobalState()
    # print table of requests in private message
    if state.priority_table != {}:
        # get user private message channel, or create if doesn't exist
        user = ctx.author
        dm_channel = user.dm_channel
        if dm_channel is None:
            await user.create_dm()
            dm_channel = user.dm_channel

        await ctx.send("Sliding into your DMs. :wink:")

        table_list = build_update_table(state.priority_table, sort_by)
        for table in table_list:
            await dm_channel.send(table)

    else:
        await ctx.send("I got nothing to show you, my dude.")


# ADMIN COMMANDS
@bot.command()
@has_role(ADMIN_ROLE)
@save_state
async def newraid(ctx):
    # initialize priority table and unlock soft reserves
    # TODO: reinit channel
    state = GlobalState()
    # Save the ID of the user initiating the newraid. Only they will be able to set it up
    state.new_raid_user_id = ctx.author.id

    user = ctx.author
    user_dm = user.dm_channel
    if user_dm is None:
        await user.create_dm()
        user_dm = user.dm_channel

    s = NEW_RAID_SPLIT_TOKEN
    c = NEW_RAID_CANCEL_TRIGGER

    msg = (
        f"To initialize the new raid reply to me here with the extra info in the format below or '{c}' to cancel.\n"
        f"`<raid name> {s} <raid description> {s} <raid date> {s} <raid time>`\n\n"
        "Date and time should be formatted as: dd/mm/yyyy and hh:mm\n"
        "All times are assumed to be in 24h format and being server time.\n"
        "For example:\n"
        f"`Molten Core Full Clear {s} Lets clear MC again! {s} 13/02/2069 {s} 19:30`"
    )
    await user_dm.send(msg)
    await ctx.message.delete()


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


@bot.command(rest_is_raw=True)
@has_role(ADMIN_ROLE)
async def boss(ctx, *, boss_id):
    boss_id = boss_id.strip()

    # boss_id is either: 1 or majordomo executus
    if not boss_id:
        await ctx.send("Am I supposed to guess? What boss do you want?")
        return

    potential_loot = None
    boss_name = None
    if boss_id.isdigit():
        # Boss identified by his number
        boss_number = int(boss_id) - 1
        if boss_number not in range(len(MC_BOSS_NAMES)):
            await ctx.send("Not a real number. Do I have to spell everything out?")
            return
        else:
            boss_name = MC_BOSS_NAMES[boss_number]
            potential_loot = MC_BOSS_LOOT[boss_name]
    else:
        if len(boss_id) < 3:
            await ctx.send("Wtf kinda name is that?")
            return
        # Boss identified by name
        for name in MC_BOSS_NAMES:
            if boss_id.casefold() in name:
                boss_name = name
                potential_loot = MC_BOSS_LOOT[boss_name]
                break
        else:
            await ctx.send("No boss with that name found. Type better.")
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
    table_list = build_update_table(RELEVANT_TABLE)
    await ctx.send("**" + boss_name.title() + "**")
    for table in table_list:
        await ctx.send(table)


@bot.command(rest_is_raw=True)
@has_role(ADMIN_ROLE)
@save_state
async def itemwin(ctx, *, character_name):
    character_name = character_name.strip()

    state = GlobalState()
    try:
        state.priority_table[character_name.casefold()].received_item = True
        await ctx.send(f"Congrats, {character_name}!")
    except KeyError:
        await ctx.send("I don't know this person. :frowning:")


@bot.command()
@has_role(ADMIN_ROLE)
async def winners(ctx):
    state = GlobalState()
    if state.priority_table != {}:
        WINNERS = {}
        for player_name, request in state.priority_table.items():
            if request.received_item:
                WINNERS[player_name] = state.priority_table[player_name]
        table_list = build_update_table(WINNERS)
        for table in table_list:
            await ctx.send(table)


if __name__ == "__main__":
    logging.basicConfig(
        filename=f"{path.dirname(path.abspath(__file__))}/lootbot.log",
        level=logging.INFO,
        filemode='a',
        format="%(levelname)s:%(name)s:[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.info(" ")
    logging.info("-" * 50)
    logging.info(" ")

    GlobalState().load_current_saved_state()
    GlobalState().boot_time = datetime.now()

    try:
        bot.run(DISCORD_TOKEN)
    except RuntimeError:
        logger.info("Exiting messily.")
    except Exception as e:
        logger.info(e)
