token = "rho sucks at using filters"
channel_name = "general"

SAVE_FILEPATH = "current_raid.exe"
PREVIOUS_SAVE_FILEPATH = "previous_raid.exe"


try:
    from local_settings import *  # NOQA
except ImportError:
    print("No local_settings.py file")
    print("Get your own token!")
