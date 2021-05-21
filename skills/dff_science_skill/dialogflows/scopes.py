from enum import Enum, auto

MAIN = "SYSTEM"
SCIENCE = "SCIENCE"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
