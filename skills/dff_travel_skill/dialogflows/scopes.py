from enum import Enum, auto

MAIN = "SYSTEM"
TRAVEL = "TRAVEL"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
