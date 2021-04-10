from enum import Enum, auto

MAIN = "SYSTEM"
ANIMALS = "ANIMALS"
USER_PETS = "USER_PETS"
MY_PETS = "MY_PETS"
WILD_ANIMALS = "WILD_ANIMALS"


class State(Enum):
    USR_ROOT = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
