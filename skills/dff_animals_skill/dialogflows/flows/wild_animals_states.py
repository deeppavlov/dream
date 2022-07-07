from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_ANIMAL_Q = auto()
    USR_ANIMAL_Q = auto()
    #
    SYS_ANIMAL_F = auto()
    USR_ANIMAL_F = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
