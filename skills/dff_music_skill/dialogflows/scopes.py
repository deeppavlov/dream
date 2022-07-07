from enum import Enum, auto

MAIN = "SYSTEM"
MUSIC = "MUSIC"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
