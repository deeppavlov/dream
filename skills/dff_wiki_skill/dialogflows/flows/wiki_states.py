from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_TELL_FACT = auto()
    USR_TELL_FACT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
