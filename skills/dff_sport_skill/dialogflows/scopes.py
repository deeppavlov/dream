from enum import Enum, auto

MAIN = "SYSTEM"
SPORT = "SPORT"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
