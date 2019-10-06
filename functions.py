import discord
from beautifultable import BeautifulTable

from info import AUTHOR, SOURCE, INVITE


def build_table_str(DICTIONARY, headers):
    table = BeautifulTable()
    table.column_headers = headers
    for key in DICTIONARY.keys():
        time = DICTIONARY[key][2]
        table.append_row([key, ] + DICTIONARY[key][:2] + ["{:02d}:{:02d}:{:02d}".format(time.hour, time.minute, time.second), ])
    table.sort("Item Requested")
    table = "```" + str(table) + "```"
    return table


def write_info():
    embed = discord.Embed(title="Loot Priority Bot", description="Waaaaay better than writing everything by hand, wouldn't you agree?")
    embed.add_field(name="Authors", value=AUTHOR)
    embed.add_field(name="Source", value=SOURCE)
    embed.add_field(name="Invite", value=INVITE)
    return embed


def write_help():
    embed_pleb = write_help_pleb()
    embed_admin = write_help_admin()
    return embed_pleb, embed_admin


def write_help_admin():
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
    return embed_admin


def write_help_pleb():
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
    return embed_pleb
