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
    SYS_PLAY_WITH_PET = auto()
    SYS_LIKE_PET = auto()
    SYS_ASK_MORE_INFO = auto()
    SYS_ANOTHER_PET = auto()
    #
    USR_ASK_ABOUT_NAME = auto()
    USR_WHAT_BREED = auto()
    USR_PLAY_WITH_PET = auto()
    USR_LIKE_PET = auto()
    USR_ASK_MORE_INFO = auto()
    USR_ANOTHER_PET = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
