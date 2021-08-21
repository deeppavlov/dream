from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_ABOUT_PET = auto()
    #
    USR_ABOUT_PET = auto()
    #
    SYS_MY_PET = auto()
    #
    USR_MY_PET = auto()
    #
    SYS_END = auto()
    #
    USR_END = auto()
    #
    SYS_WHAT_ANIMALS = auto()
    SYS_Q_HAVE_PETS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
