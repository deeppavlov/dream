from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_WHAT_ANIMALS = auto()
    SYS_DO_YOU_HAVE = auto()
    SYS_WHAT_WILD_ANIMALS = auto()
    SYS_LIKE_ANIMALS = auto()
    SYS_MENTION_PETS = auto()
    #
    USR_WHAT_ANIMALS = auto()
    USR_HAVE_PETS = auto()
    USR_WHAT_WILD_ANIMALS = auto()
    USR_MENTION_PETS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
