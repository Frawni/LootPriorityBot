DISCORD_TOKEN = "rho sucks at using filters"

PREFIX = ">"
ADMIN_ROLE = "Officer"

INFO_CHANNEL_NAME = "loot-info"
REQUEST_CHANNEL_NAME = "loot-request"
DISCUSSION_CHANNEL_NAME = "loot-discussion"

AUTHORIZED_CHANNELS = [
    INFO_CHANNEL_NAME,
    REQUEST_CHANNEL_NAME,
    DISCUSSION_CHANNEL_NAME
]

SAVE_FILENAME = "current_raid.exe"
PREVIOUS_SAVE_FILENAME = "previous_raid.exe"


HEADERS = ["Name", "Role", "Class", "Item Requested",
           "Time of Request (UTC)", "Received Item?"]

# rewritten here in order to guarantee ordering
MC_BOSS_NAMES = ["lucifron", "magmadar", "gehennas", "garr",
                 "shazzrah", "baron geddon", "golemagg the incinerator",
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
