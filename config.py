ADMIN_ROLE = "tourist"


HELLO_TRIGGER = "!hello"

NEWRAID_TRIGGER = "!newraid"
SOFTRESERVE_TRIGGER = "!soft"
LOCK_TRIGGER = "!lock"
UNLOCK_TRIGGER = "!unlock"
SHOWTABLE_TRIGGER = "!show"
BOSSLOOT_TRIGGER = "!boss"

HELP_TRIGGER = "!help"


HELP_MESSAGE_PLEB = """
Here is a list of commands you have access to:\n
**{}** : show this message (helpful, I know)
**{}** <character name>/<class>/<item name> : request an item for the current raid
**{}** : show the table of requests
**{}** : show the items already requested for this boss
""".format(HELP_TRIGGER, SOFTRESERVE_TRIGGER, SHOWTABLE_TRIGGER, BOSSLOOT_TRIGGER)

HELP_MESSAGE_ADMIN = """
Just 'cause you're special, here are extra commands,
just for you (and a couple of others)! :kissing_heart:\n
**{}** : resets the request table and everything
**{}** : locks requests - no new ones accepted
**{}** : you done goofed and people need to change stuff? No problem!
""".format(NEWRAID_TRIGGER, LOCK_TRIGGER, UNLOCK_TRIGGER)
