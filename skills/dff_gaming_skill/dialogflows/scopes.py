from enum import Enum, auto

MAIN = "SYSTEM"
GAMING = "GAMING"
MINECRAFT = "MINECRAFT"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
