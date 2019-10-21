import logging
import json
import discord
from typing import List
from dataclasses import dataclass, field, asdict, fields
from datetime import datetime
from os import path

from settings import SAVE_FILENAME, PREVIOUS_SAVE_FILENAME

logger = logging.getLogger(__name__)


ABSOLUTE_CURRENT_SAVE_FP = path.join(path.dirname(path.abspath(__file__)), SAVE_FILENAME)
ABSOLUTE_PREVIOUS_SAVE_FP = path.join(path.dirname(path.abspath(__file__)), PREVIOUS_SAVE_FILENAME)


@dataclass
class Request:
    role: str
    wow_class: str
    item: str
    datetime: datetime
    received_item: bool

    def as_presentable(self):
        data = {k: v.title() if isinstance(v, str) else v for k, v in asdict(self).items()}
        return Request(**data)


class SingletonMetaclass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class GlobalState(metaclass=SingletonMetaclass):
    """
    Class that holds all the global state variables used by the bot.
    Though there arent any explcit static methods/variables, the metaclass enforces the singleton pattern.
    Any instantiation of this class with return the same instance of this class.

    ! NOT THREAD SAFE !
    """

    """Attributes that will be serialized/saved to disk"""
    # "<name>": Request recordclass
    priority_table: dict = field(default_factory=dict)
    # bool (true when locked, false when unlocked)
    lock_flag: bool = field(default=True)
    # Prevent spam --> PM if less than an hour in channel
    last_help: datetime = field(default=None)
    # When the raid was created with "!newraid"
    created: datetime = field(default=None)
    # Id of user who has initiated the newraid command and who must fill in the info in DMs
    new_raid_user_id: int = field(default=None)
    # Attributes of the raid itself
    name: str = field(default=None)
    description: str = field(default=None)
    when: datetime = field(default=None)

    # The messages are serialized as their IDs and then converted Message objects in the bots on_readY()
    # Message id of the updating messages posted in the info channel
    status_message: discord.Message = field(default=None)
    table_messages: List[discord.Message] = field(default_factory=list)

    """Attributes that shouldnt be serialized/saved"""
    # Reference to the discord info channel for message deleting
    initialized = False
    info_channel = None
    boot_time = None

    def load_current_saved_state(self):
        try:
            with open(ABSOLUTE_CURRENT_SAVE_FP, "r") as f:
                saved_state = json_load(f)
                saved_state["priority_table"] = {
                    k: Request(**v)
                    for k, v in saved_state["priority_table"].items()
                }
            self.__init__(**saved_state)
        except FileNotFoundError:
            logger.info("No save file found")

    def save_current_state(self):
        with open(ABSOLUTE_CURRENT_SAVE_FP, "w") as f:
            json_dump(self, f)

    def new_raid(self, name, description, when):
        with open(ABSOLUTE_PREVIOUS_SAVE_FP, "w") as f:
            json_dump(self, f)
        self.__init__(
            name=name, description=description, when=when,
            lock_flag=False, last_help=self.last_help, created=datetime.now(),
            status_message=self.status_message, table_messages=self.table_messages
        )
        return self


"""
Json loading/dumping wrappers in order to take care of datetimes/dataclasses
"""


def json_load(fp):
    """
    Custom json.load that automatically converts isoformat strings to their corresponding datetime object
    """
    def json_custom_deserializer(pairs):
        res = {}
        for k, v in pairs:
            if isinstance(v, str):
                try:
                    res[k] = datetime.fromisoformat(v)
                except ValueError:
                    res[k] = v
            else:
                res[k] = v
        return res

    return json.load(fp, object_pairs_hook=json_custom_deserializer)


def json_dump(obj, fp):
    """
    Custom json.dump that automatically converts datetime objects to isoformat strings and converts
        dataclasses to their dictionary representations
    """
    def json_custom_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Request):
            return asdict(obj)
        if isinstance(obj, GlobalState):
            # We do this rather than using asdict() as that tries to deepcopy the values returned
            #   This fails spectacularly for the discord.Message object
            return {field.name: getattr(obj, field.name) for field in fields(obj)}
        if isinstance(obj, discord.Message):
            return obj.id

    return json.dump(obj, default=json_custom_serializer, fp=fp)
