from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_ABOUT_CAT = auto()
    SYS_ABOUT_DOG = auto()
    #
    USR_ABOUT_CAT = auto()
    USR_ABOUT_DOG = auto()
    #
    SYS_MY_CAT_1 = auto()
    SYS_MY_DOG_1 = auto()
    #
    USR_MY_CAT_1 = auto()
    USR_MY_DOG_1 = auto()
    #
    SYS_MY_CAT_2 = auto()
    SYS_MY_DOG_2 = auto()
    #
    USR_MY_CAT_2 = auto()
    USR_MY_DOG_2 = auto()
    #
    SYS_MY_CAT_3 = auto()
    SYS_MY_DOG_3 = auto()
    #
    USR_MY_CAT_3 = auto()
    USR_MY_DOG_3 = auto()
    #
    SYS_WHAT_ANIMALS = auto()
    SYS_Q_HAVE_PETS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
