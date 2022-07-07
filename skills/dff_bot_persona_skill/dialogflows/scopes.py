from enum import Enum, auto

MAIN = "SYSTEM"
BOT_PERSONA = "BOT_PERSONA"
# STARTER = "STARTER"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
