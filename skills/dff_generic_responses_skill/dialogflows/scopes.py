from enum import Enum, auto

MAIN = "SYSTEM"
GENERIC_RESPONSES = "GENERIC_RESPONSES"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
