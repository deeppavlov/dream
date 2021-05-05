from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_FAV_OR_LETS_CHAT = auto()
    USR_MY_FAV_STORY = auto()
    SYS_CHECK_FAV = auto()
    USR_DO_YOU_LIKE_TOPIC = auto()
    SYS_LIKE_TOPIC = auto()
    SYS_NOT_LIKE_TOPIC = auto()
    USR_WHATS_YOUR_FAV = auto()
    USR_TOP_FAVS = auto()
    SYS_WHY_FAV = auto()
    USR_EXPLAIN_FAV = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
