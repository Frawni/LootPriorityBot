# Author: Caroline Forest
# Last updated: 5th Oct 2019

"""
BARE MINIMUM
- !help --> rewrite for the love of all that is holy
- !show --> prevent spam by checking time; better display
- !boss

PRETTY
- divide into manageable files for accessibility

POTENTIAL EXCEPTIONS (to be dealt with)
- CommandNotFound (l 50)
- MissingRole (ll 50, 85, 94)
"""


import discord
from discord.ext.commands import Bot, has_role
from datetime import datetime
from beautifultable import BeautifulTable

from config import AUTHORIZED_CHANNELS, ADMIN_ROLE, PREFIX
from settings import token
from info import AUTHOR, SOURCE, INVITE


# GLOBAL VARIABLES
bot = Bot(command_prefix=PREFIX)
bot.remove_command("help")

PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item with spaces>", "UTC datetime"]
lock_flag = 0            # bool

# Prevent spam --> PM if less than an hour in channel
last_help = None   # last help command run in channel


@bot.event
async def on_ready():
    print("We have logged in as {}".format(bot.user.name))


@bot.event
async def on_message(message):
    channel = message.channel
    if channel.type == discord.ChannelType.private:
        return
    elif channel.name in AUTHORIZED_CHANNELS:
        await bot.process_commands(message)      # maybe deal with CommandNotFound? but so far doesn't break, just 'logs'


@bot.command()
async def hello(ctx):
    await ctx.send("Greetings!")


@bot.command()
async def info(ctx):
    embed = discord.Embed(title="Loot Priority Bot", description="Waaaaay better than writing everything by hand, wouldn't you agree?")
    embed.add_field(name="Authors", value=AUTHOR)
    embed.add_field(name="Source", value=SOURCE)
    embed.add_field(name="Invite", value=INVITE)
    await ctx.send(embed=embed)


@bot.command()
async def help(ctx):
    # spam filter of 1 hour
    global last_help
    print(last_help)
    embed_pleb = discord.Embed(
        title="Loot Priority Bot",
        description="A list of basic commands:"
    )
    embed_pleb.add_field(
        name="!request <name>/<class>/<item>",
        value="Request priority on an item for the upcoming raid\nIf your name is already on the list, will replace the previous item",
        inline=False
    )
    embed_pleb.add_field(
        name="!show",
        value="Sends you the table of existing requests",
        inline=False
    )
    embed_pleb.add_field(
        name="!info",
        value="Authors, source code link, invite link",
        inline=False
    )
    embed_pleb.add_field(
        name="!help",
        value="Whaddya think?",
        inline=False
    )
    embed_admin = discord.Embed(
        title="Extra commands for the privileged."
    )
    embed_admin.add_field(
        name="!newraid",
        value="Resets the list of requests and unlocks the request command",
        inline=False
    )
    embed_admin.add_field(
        name="!showall",
        value="Shows the table of requested items in the channel",
        inline=False
    )
    embed_admin.add_field(
        name="!boss",
        value="Shows the table for items relevant to that boss",
        inline=False
    )
    embed_admin.add_field(
        name="!lock",
        value="Locks requests - no new ones accepted",
        inline=False
    )
    embed_admin.add_field(
        name="!unlock",
        value="You done goofed and people need to change stuff? No problem!",
        inline=False
    )
    if last_help is not None:
        delta = datetime.utcnow() - last_help
        print(delta)
        if delta.days == 0 and delta.seconds < 3600:
            user = ctx.author
            dm_channel = user.dm_channel
            if dm_channel is None:
                await user.create_dm()
                dm_channel = user.dm_channel
            await ctx.send("Sliding into your DMs :wink:")
            await dm_channel.send(embed=embed_pleb)
            await dm_channel.send(embed=embed_admin)
        else:
            await ctx.send(embed=embed_pleb)
            await ctx.send(embed=embed_admin)
            last_help = datetime.utcnow()
    else:
        await ctx.send(embed=embed_pleb)
        await ctx.send(embed=embed_admin)
        last_help = datetime.utcnow()


@bot.command()
@has_role(ADMIN_ROLE)
async def newraid(ctx):
    # initialize priority table and unlock soft reserves
    global PRIORITY_TABLE, lock_flag
    PRIORITY_TABLE = {}
    lock_flag = 0
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
        info = request.split("/")
        PRIORITY_TABLE[info[0]] = info[1:] + [datetime.utcnow(), ]
        reply = "Noted!"
    else:
        reply = "Raid priority is locked. Sorry!"
    await ctx.send(reply)


@bot.command()
@has_role(ADMIN_ROLE)
async def lock(ctx):
    # raise flag for no more soft reserves
    global lock_flag
    lock_flag = 1
    await ctx.send("Raid priority is now locked!")


@bot.command()
@has_role(ADMIN_ROLE)
async def unlock(ctx):
    # lower flag for more soft reserves
    global lock_flag
    lock_flag = 0
    await ctx.send("Raid priority is open once more!")


@bot.command()
async def show(ctx):
    table = BeautifulTable()
    table.column_headers = ["Name", "Class", "Item Requested", "Time of Request (UTC)"]
    for key in PRIORITY_TABLE.keys():
        time = PRIORITY_TABLE[key][2]
        table.append_row([key, ] + PRIORITY_TABLE[key][:2] + ["{:02d}:{:02d}:{:02d}".format(time.hour, time.minute, time.second), ])
    user = ctx.author
    dm_channel = user.dm_channel
    if dm_channel is None:
        await user.create_dm()
        dm_channel = user.dm_channel
    await ctx.send("Sliding into your DMs :wink:")
    await dm_channel.send("\n" + str(table))


@bot.command()
@has_role(ADMIN_ROLE)
async def showall(ctx):
    # print table of requests
    # spam-filter of 1 minute if requests unlock
    table = BeautifulTable()
    table.column_headers = ["Name", "Class", "Item Requested", "Time of Request (UTC)"]
    for key in PRIORITY_TABLE.keys():
        time = PRIORITY_TABLE[key][2]
        table.append_row([key, ] + PRIORITY_TABLE[key][:2] + ["{:02d}:{:02d}:{:02d}".format(time.hour, time.minute, time.second), ])
    await ctx.send("\n" + str(table))


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
