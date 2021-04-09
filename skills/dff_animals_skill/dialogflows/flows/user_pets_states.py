from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_WHAT_PETS = auto()
    SYS_IS_DOG_CAT = auto()
    SYS_NOT_HAVE = auto()
    #
    USR_WHAT_PETS = auto()
    USR_ASK_ABOUT_DOG_CAT = auto()
    USR_NOT_HAVE = auto()
    #
    SYS_ASK_ABOUT_NAME = auto()
    SYS_WHAT_BREED = auto()
    SYS_WHAT_COLOR = auto()
    SYS_ASK_ABOUT_FEEDING = auto()
    #
    USR_ASK_ABOUT_NAME = auto()
    USR_WHAT_BREED = auto()
    USR_WHAT_COLOR = auto()
    USR_ASK_ABOUT_FEEDING = auto()
    #
    SYS_TELL_FACT_ABOUT_BREED = auto()
    #
    USR_TELL_FACT_ABOUT_BREED = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
