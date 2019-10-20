import discord
from tabulate import tabulate

from info import AUTHOR, SOURCE, INVITE
from settings import HEADERS


def build_table(DICTIONARY, sort_by=""):
    table = []
    table_list = []

    for key in DICTIONARY.keys():
        request = DICTIONARY[key].as_presentable()
        time = request.datetime
        time_str = "{:02d}:{:02d}:{:02d}".format(time.hour, time.minute, time.second)
        item_received = "{}".format("Yes" if request.received_item else "No")
        row = [key.title(), request.role, request.wow_class, request.item] + [time_str, item_received]
        table.append(row)

    index = HEADERS.index("Item Requested")
    if sort_by != "":
        for header in HEADERS:
            if sort_by.casefold() in header.casefold():
                index = HEADERS.index(header)
                break
        else:
            table_list.append("I'm not sure how you want me to sort this, so here are the requests by items. :grin:")

    ordered_table = sorted(table, key=lambda x: x[index])

    row_count = len(ordered_table)
    separator = 12
    i = 0

    while row_count > separator:
        table_list.append("```" + tabulate(ordered_table[(separator*i):(separator*(i+1))], headers=HEADERS, tablefmt="psql") + "```")
        row_count -= separator
        i += 1
    table_list.append("```" + tabulate(ordered_table[(separator*i):], headers=HEADERS, tablefmt="psql") + "```")

    return table_list


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
        name="!lock",
        value="Locks requests - no new ones accepted",
        inline=False
    )
    embed_admin.add_field(
        name="!unlock",
        value="You done goofed and people need to change stuff? No problem!",
        inline=False
    )
    embed_admin.add_field(
        name="!showall (<filter>)",
        value="Shows the table of requested items in the channel, same functionality as !show",
        inline=False
    )
    embed_admin.add_field(
        name="!boss",
        value="Shows the table for items relevant to that boss",
        inline=False
    )
    embed_admin.add_field(
        name="!itemwin <character name>",
        value="Records the person who won their requested item",
        inline=False
    )
    embed_admin.add_field(
        name="!winners",
        value="Shows the table for people who won their requested item",
        inline=False
    )
    return embed_admin


def write_help_pleb():
    embed_pleb = discord.Embed(
        title="Loot Priority Bot",
        description="A list of basic commands:"
    )
    embed_pleb.add_field(
        name="!request <character name>/<role> (tank|healer|dps)/<class>/<item>",
        value="Request priority on an item for the upcoming raid\nIf your name is already on the list, it will replace the previous item",
        inline=False
    )
    embed_pleb.add_field(
        name="!show (<filter>)",
        value="Sends you the table of existing requests, can add the name of the column to filter by",
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
