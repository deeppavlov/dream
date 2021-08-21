from enum import Enum, auto

MAIN = "SYSTEM"
FOOD = "FOOD"
FAST_FOOD = "FAST_FOOD"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
