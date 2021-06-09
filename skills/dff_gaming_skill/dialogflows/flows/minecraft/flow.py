import logging
from functools import partial

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention

import dialogflows.scopes as scopes

import dialogflows.flows.minecraft.intents as minecraft_intents
import dialogflows.flows.minecraft.nlg as minecraft_nlg
from dialogflows.common.intents import user_says_anything_request
from dialogflows.flows.minecraft.states import State as MinecraftState


logger = logging.getLogger(__name__)


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

simplified_dialogflow = dialogflow_extention.DFEasyFilling(MinecraftState.USR_START)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_START,
    {
        MinecraftState.SYS_USER_WANTS_TO_TALK_ABOUT_MINECRAFT:
            minecraft_intents.user_wants_to_talk_about_minecraft_request
    },
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_START, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_WANTS_TO_TALK_ABOUT_MINECRAFT,
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    partial(
        minecraft_nlg.tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response,
        candidate_game_id_is_already_set=False,
        must_continue=True,
    ),
)
simplified_dialogflow.set_error_successor(
    MinecraftState.SYS_USER_WANTS_TO_TALK_ABOUT_MINECRAFT, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    {MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT: user_says_anything_request},
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT,
    (scopes.MAIN, scopes.State.USR_ROOT),
    minecraft_nlg.praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response,
)
simplified_dialogflow.set_error_successor(
    MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT, MinecraftState.SYS_ERR)
##############################################################

simplified_dialogflow.add_global_user_serial_transitions(
    {
        MinecraftState.SYS_ERR: (lambda x, y: True, -1.0),
    },
)
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    MinecraftState,
)

dialogflow = simplified_dialogflow.get_dialogflow()
