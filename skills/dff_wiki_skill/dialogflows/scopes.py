from enum import Enum, auto

MAIN = "SYSTEM"
WIKI = "WIKI"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
