from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_WHY_DO_YOU_LIKE = auto()
    #
    USR_WHY_DO_YOU_LIKE = auto()
    #
    SYS_ASK_ABOUT_ZOO = auto()
    #
    USR_ASK_ABOUT_ZOO = auto()
    #
    SYS_USER_HAS_BEEN = auto()
    SYS_USER_HAS_NOT_BEEN = auto()
    #
    USR_ASK_MORE_DETAILS = auto()
    USR_SUGGEST_VISITING = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
