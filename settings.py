DISCORD_TOKEN = "rho sucks at using filters"

PREFIX = ">"
ADMIN_ROLE = "Loot Master"

MC_INFO_CHANNEL_NAME = "mc-loot-info"
BWL_INFO_CHANNEL_NAME = "bwl-loot-info"
MC_REQUEST_CHANNEL_NAME = "mc-loot-request"
BWL_REQUEST_CHANNEL_NAME = "bwl-loot-request"
DISCUSSION_CHANNEL_NAME = "loot-discussion"

NUM_MESSAGES_FOR_TABLE = 5
RESERVED_MESSAGE_TEXT = "~Message reserved for loot table~"

AUTHORIZED_CHANNELS = [
    MC_INFO_CHANNEL_NAME,
    MC_REQUEST_CHANNEL_NAME,
    BWL_INFO_CHANNEL_NAME,
    BWL_REQUEST_CHANNEL_NAME,
    DISCUSSION_CHANNEL_NAME
]

MC_SAVE_FILENAME = "mc_current_raid.exe"
MC_PREVIOUS_SAVE_FILENAME = "mc_previous_raid.exe"
BWL_SAVE_FILENAME = "bwl_current_raid.exe"
BWL_PREVIOUS_SAVE_FILENAME = "bwl_previous_raid.exe"

NEW_RAID_CANCEL_TRIGGER = "cancel"
NEW_RAID_SPLIT_TOKEN = "|"

# rewritten here in order to guarantee ordering
MC_BOSS_NAMES = ["lucifron", "magmadar", "gehennas", "garr",
                 "baron geddon", "shazzrah", "golemagg the incinerator",
                 "sulfuron harbringer", "majordomo executus", "ragnaros"]

BWL_BOSS_NAMES = ["razergore the untamed", "vaelastrasz the corrupt",
                  "broodlord lashlayer", "firemaw", "ebonroc",
                  "flamegor", "chromaggus", "nefarian"]

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
