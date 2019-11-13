DISCORD_TOKEN = "rho sucks at using filters"

PREFIX = ">"
ADMIN_ROLE = "Loot Master"

INFO_CHANNEL_NAME = "loot-info"
REQUEST_CHANNEL_NAME = "loot-request"
DISCUSSION_CHANNEL_NAME = "loot-discussion"

NUM_MESSAGES_FOR_TABLE = 5
RESERVED_MESSAGE_TEXT = "~Message reserved for loot table~"

AUTHORIZED_CHANNELS = [
    INFO_CHANNEL_NAME,
    REQUEST_CHANNEL_NAME,
    DISCUSSION_CHANNEL_NAME
]

SAVE_FILENAME = "current_raid.exe"
PREVIOUS_SAVE_FILENAME = "previous_raid.exe"

NEW_RAID_CANCEL_TRIGGER = "cancel"
NEW_RAID_SPLIT_TOKEN = "|"

# rewritten here in order to guarantee ordering
MC_BOSS_NAMES = ["lucifron", "magmadar", "gehennas", "garr",
                 "baron geddon", "shazzrah", "golemagg the incinerator",
                 "sulfuron harbringer", "majordomo executus", "ragnaros"]

WOW_CLASSES = [
    "druid",
    "hunter",
    "mage",
    "paladin",
    "priest",
    "rogue",
    "warlock",
    "warrior",
]

WOW_ROLES = [
    "tank",
    "healer",
    "dps"
]

try:
    from local_settings import *  # NOQA
except ImportError:
    print("No local_settings.py file")

try:
    from local_settings import DISCORD_TOKEN  # NOQA
except ImportError:
    print("Get your own token!")
    exit()
