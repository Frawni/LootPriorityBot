import discord
import tabulate as tb

from info import AUTHOR, SOURCE, INVITE
from globals import GlobalState
from settings import NUM_MESSAGES_FOR_TABLE, PREFIX, RESERVED_MESSAGE_TEXT

tb.PRESERVE_WHITESPACE = True


def write_info():
    state = GlobalState()
    embed = discord.Embed(title="Loot Priority Bot",
                          description="Waaaaay better than writing everything by hand, wouldn't you agree?")
    embed.add_field(name="Authors", value=AUTHOR)
    embed.add_field(name="Source", value=SOURCE)
    embed.add_field(name="Invite", value=INVITE)
    embed.add_field(name="Last Booted", value=f"{state.boot_time}")
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
        name=f"{PREFIX}newraid",
        value="Resets the list of requests and unlocks the request command",
        inline=False
    )
    embed_admin.add_field(
        name=f"{PREFIX}lock",
        value="Locks requests - no new ones accepted",
        inline=False
    )
    embed_admin.add_field(
        name=f"{PREFIX}unlock",
        value="You done goofed and people need to change stuff? No problem!",
        inline=False
    )
    embed_admin.add_field(
        name=f"{PREFIX}boss <name/number>",
        value="Shows the table for items relevant to that boss",
        inline=False
    )
    embed_admin.add_field(
        name=f"{PREFIX}itemwin <character name>",
        value="Records the person who won their requested item",
        inline=False
    )
    embed_admin.add_field(
        name=f"{PREFIX}winners",
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
        name=f"{PREFIX}request <character name>/<role> (tank|healer|dps)/<class>/<item>",
        value="Request priority on an item for the upcoming raid\nIf your name is already on the list, it will replace the previous item",
        inline=False
    )
    embed_pleb.add_field(
        name=f"{PREFIX}show (<filter>)",
        value="Sends you the table of existing requests, can add the name of the column to filter by",
        inline=False
    )
    embed_pleb.add_field(
        name=f"{PREFIX}info",
        value="Authors, source code link, invite link",
        inline=False
    )
    embed_pleb.add_field(
        name=f"{PREFIX}help",
        value="Whaddya think?",
        inline=False
    )
    return embed_pleb


async def update_status():
    state = GlobalState()

    if state.created:
        embed = discord.Embed(
            title=f"{state.name}",
            description=f"{state.description}"
        )
        embed.add_field(
            name="Raid Time",
            value=f"{state.when}",
            inline=False
        )
        embed.add_field(
            name="Player Requests",
            value=f"{len(state.priority_table)}"
        )
        embed.add_field(
            name="Request Status",
            value=f"{'LOCKED' if state.lock_flag else 'OPEN'}"
        )
    else:
        embed = discord.Embed(
            title="Nope",
            description="No raid is being tracked at the moment."
        )
    await state.status_message.edit(embed=embed, content="")


async def update_table():
    state = GlobalState()

    if state.priority_table:
        table_list = build_update_table()
        for table, message in zip(table_list, state.table_messages):
            await message.edit(content=table)

        for i in range(len(table_list), NUM_MESSAGES_FOR_TABLE):
            await state.table_messages[i].edit(content=RESERVED_MESSAGE_TEXT)
    else:
        msg = (
                "Nothing to see here... yet."
        )
        await state.table_messages[0].edit(content=msg)
        for i in range(1, NUM_MESSAGES_FOR_TABLE):
            await state.table_messages[i].edit(content=RESERVED_MESSAGE_TEXT)


def build_update_table(loot_table=None, sort_by=None):
    HEADERS = ["Name", "Role", "Class", "Item"]

    if loot_table is None:
        state = GlobalState()
        loot_table = state.priority_table

    table = []
    table_list = []

    max_name_size = max(len(name) for name in loot_table.keys())
    max_item_size = max(len(request.item) for request in loot_table.values())
    max_role_size = max(len(request.role) for request in loot_table.values())
    max_class_size = max(len(request.wow_class) for request in loot_table.values())
    max_item_size = max(len(request.item) for request in loot_table.values())

    for key in loot_table.keys():
        request = loot_table[key].as_presentable()
        row = [
            key.title().ljust(max_name_size, " "),
            request.role.ljust(max_role_size, " "),
            request.wow_class.ljust(max_class_size, " "),
            request.item.ljust(max_item_size, " "),
        ]
        table.append(row)

    if sort_by is not None and sort_by.title() in HEADERS:
        sort_column = HEADERS.index(sort_by.title())
        ordered_table = sorted(table, key=lambda x: (x[sort_column]))
    else:
        # By default we sort by (item, name)
        ordered_table = sorted(table, key=lambda x: (x[3], x[0]))

    row_count = len(ordered_table)
    rows_per_msg = 10
    i = 0
    if row_count > rows_per_msg:
        table_list.append("```" + tb.tabulate(ordered_table[(rows_per_msg*i):(rows_per_msg*(i+1))], headers=HEADERS, tablefmt="fancy_grid", ) + "```")
        row_count -= rows_per_msg
        i += 1
    else:
        table_list.append("```" + tb.tabulate(ordered_table[(rows_per_msg*i):], headers=HEADERS, tablefmt="fancy_grid", ) + "```")
        return table_list

    while row_count > rows_per_msg:
        table_list.append("```" + tb.tabulate(ordered_table[(rows_per_msg*i):(rows_per_msg*(i+1))], tablefmt="fancy_grid", ) + "```")
        row_count -= rows_per_msg
        i += 1
    table_list.append("```" + tb.tabulate(ordered_table[(rows_per_msg*i):], tablefmt="fancy_grid", ) + "```")

    return table_list


async def init_update_messages(channel):
    state = GlobalState()
    state.table_messages = []
    state.status_message = await channel.send("I'm bootin' baby!")
    for i in range(NUM_MESSAGES_FOR_TABLE):
        state.table_messages.append(await channel.send(RESERVED_MESSAGE_TEXT))
