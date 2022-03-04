from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    # SYS_GENRE = auto()
    # USR_GENRE = auto()
    # SYS_WEEKDAY = auto()
    USR_WHAT_FAV = auto()
    SYS_CHECK_POSITIVE = auto()
    SYS_CHECK_NEGATIVE = auto()
    SYS_CHECK_NEUTRAL = auto()
    SYS_GET_REASON = auto()
    USR_REPEAT = auto()
    SYS_AGREED = auto()
    SYS_DISAGREED = auto()
    USR_ASSENT_YES = auto()
    USR_ASSENT_NO = auto()
    USR_MY_FAV = auto()
    SYS_YES = auto()
    SYS_NO = auto()
    USR_WHY = auto()
    USR_MY_FAV_STORY = auto()
    # USR_WEEKDAY = auto()
    SYS_FRIDAY = auto()
    USR_FRIDAY = auto()
    SYS_SMTH = auto()
    USR_MY_FAV_DAY = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
