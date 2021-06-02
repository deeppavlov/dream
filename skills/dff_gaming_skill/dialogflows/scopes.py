from enum import Enum, auto

MAIN = "SYSTEM"
GAMING = "GAMING"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
