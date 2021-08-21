from enum import Enum, auto

MAIN = "SYSTEM"
GREETING = "GREETING"
REPEATING = "REPEATING"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
