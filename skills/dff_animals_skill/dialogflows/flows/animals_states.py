from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_WHAT_ANIMALS = auto()
    SYS_Q_HAVE_PETS = auto()
    SYS_WHAT_WILD_ANIMALS = auto()
    SYS_HAVE_PETS = auto()
    SYS_LIKE_ANIMALS = auto()
    SYS_MENTION_ANIMALS = auto()
    #
    USR_WHAT_ANIMALS = auto()
    USR_HAVE_PETS = auto()
    USR_TELL_ABOUT_PETS = auto()
    USR_WHAT_WILD_ANIMALS = auto()
    USR_MENTION_ANIMALS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
