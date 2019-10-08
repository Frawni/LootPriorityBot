PREFIX = "!"

ADMIN_ROLE = "tourist"

AUTHORIZED_CHANNELS = ["mc-reserve-list", ]


PRIORITY_TABLE = {}      # "<name>": ["<class>", "<item>", UTC datetime, received_item bool]
CLASS = 0
ITEM = 1
DATE = 2
RECEIVED = 3
HEADERS = ["Name", "Class/Role", "Item Requested",
           "Time of Request (UTC)", "Received Item?"]
