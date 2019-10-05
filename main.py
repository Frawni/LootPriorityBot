# Author: Caroline Forest
# Last updated: 5th Oct 2019

"""
BARE MINIMUM
- !show --> prevent spam by checking time; better display
- !boss

POTENTIAL EXCEPTIONS (to be dealt with)
- CommandNotFound (l 38)
- MissingRole (ll 50, 85, 94)
"""


import discord
from discord.ext.commands import Bot, has_role
from datetime import datetime

from config import AUTHORIZED_CHANNELS, ADMIN_ROLE
from settings import token
from info import AUTHOR, SOURCE, INVITE

bot = Bot(command_prefix='!')
bot.remove_command("help")

PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item with spaces>", "UTC datetime"]
lock_flag = 0


@bot.event
async def on_ready():
    print("We have logged in as {}".format(bot.user.name))


@bot.event
async def on_message(message):
    channel = message.channel
    if channel.name in AUTHORIZED_CHANNELS:
        await bot.process_commands(message)      # maybe deal with CommandNotFound? but so far doesn't break, just 'logs'
    elif channel.type == discord.ChannelType.private:
        await channel.send("Whatever you say, darling.")


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
    embed = discord.Embed(
        title="Loot Priority Bot",
        description="A list of basic commands:"
    )
    embed.add_field(
        name="!request <name>/<class>/<item>",
        value="Request priority on an item for the upcoming raid\nIf your name is already on the list, will replace the previous item",
        inline=False
    )
    embed.add_field(
        name="!show",
        value="Shows the table of existing requests",
        inline=False
    )
    embed.add_field(
        name="!boss",
        value="Shows the table for items relevant to that boss",
        inline=False
    )
    embed.add_field(
        name="!info",
        value="Authors, source code link, invite link",
        inline=False
    )
    embed.add_field(
        name="!help",
        value="Whaddya think?",
        inline=False
    )
    await ctx.send(embed=embed)
    embed = discord.Embed(
        title="Extra commands for the privileged."
    )
    embed.add_field(
        name="!newraid",
        value="Resets the list of requests and unlocks the request command",
        inline=False
    )
    embed.add_field(
        name="!lock",
        value="Locks requests - no new ones accepted",
        inline=False
    )
    embed.add_field(
        name="!unlock",
        value="You done goofed and people need to change stuff? No problem!",
        inline=False
    )
    await ctx.send(embed=embed)


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
        request = " ".join(list(args))
        info = request.split("/")

        # WEIRD HACKY THING BEFORE EUREKA, KEEPING CAUSE I HOARD
        # if "/" in args[0]:
        #     info = args[0].split("/") + list(args[1:])
        #     info[2] = " ".join(info[2:])
        # else:
        #     info = list(args)
        #     info[2] = " ".join(info[2:])

        PRIORITY_TABLE[info[0]] = info[1:] + [datetime.utcnow()]
        reply = "You have your heart set on this item: [link]."
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
    # print table of reserves
    # prevent spam of table by limiting to once every minute or so?
    await ctx.send("| Name | Class | Item Requested | Time of Request |")
    for key in PRIORITY_TABLE.keys():
        await ctx.send("| {} | {} | {} | {} |".format(key, *PRIORITY_TABLE[key]))


@bot.command()
async def boss(ctx):
    pass


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
