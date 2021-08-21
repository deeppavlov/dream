import logging
import os
from functools import partial

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming

import dialogflows.scopes as scopes

import dialogflows.flows.minecraft.intents as minecraft_intents
import dialogflows.flows.minecraft.nlg as minecraft_nlg
from dialogflows.common.intents import user_doesnt_say_yes_request, user_says_anything_request, user_says_yes_request
from dialogflows.flows.minecraft.states import State as MinecraftState


logger = logging.getLogger(__name__)


MINECRAFT_HOW_TOS = common_gaming.load_json(os.getenv("MINECRAFT_HOW_TOS"))


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

simplified_dialogflow = dialogflow_extension.DFEasyFilling(MinecraftState.USR_START)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_START,
    {
        MinecraftState.SYS_USER_WANTS_TO_TALK_ABOUT_MINECRAFT: minecraft_intents.user_wants_to_talk_about_minecraft_request
    },
)
simplified_dialogflow.set_error_successor(MinecraftState.USR_START, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_WANTS_TO_TALK_ABOUT_MINECRAFT,
    MinecraftState.USR_ASK_USER_WHEN_HE_STARTED_TO_PLAY_MINECRAFT,
    partial(
        minecraft_nlg.ask_user_when_he_started_to_play_minecraft_response,
        candidate_game_id_is_already_set=False,
    ),
)
simplified_dialogflow.set_error_successor(MinecraftState.SYS_USER_WANTS_TO_TALK_ABOUT_MINECRAFT, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_ASK_USER_WHEN_HE_STARTED_TO_PLAY_MINECRAFT,
    {
        MinecraftState.SYS_USER_TELLS_WHEN_HE_STARTED_TO_PLAY_MINECRAFT: partial(
            user_says_anything_request,
            additional_check=lambda n, v: len(MINECRAFT_HOW_TOS)
            - len(state_utils.get_shared_memory(v).get("used_how_to_indices", []))
            >= 1,
        ),
        MinecraftState.SYS_USER_TELLS_WHEN_HE_STARTED_TO_PLAY_MINECRAFT_AND_NO_HOW_TOS_LEFT: partial(
            user_says_anything_request,
            additional_check=lambda n, v: len(MINECRAFT_HOW_TOS)
            - len(state_utils.get_shared_memory(v).get("used_how_to_indices", []))
            < 1,
        ),
    },
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_ASK_USER_WHEN_HE_STARTED_TO_PLAY_MINECRAFT, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_TELLS_WHEN_HE_STARTED_TO_PLAY_MINECRAFT,
    MinecraftState.USR_COMMENT_ON_USER_EXPERIENCE_AND_ASK_IF_USER_WANTS_TO_KNOW_HOW_TO,
    minecraft_nlg.comment_on_user_experience_and_ask_if_user_wants_to_know_how_to_response,
)
simplified_dialogflow.set_error_successor(
    MinecraftState.SYS_USER_TELLS_WHEN_HE_STARTED_TO_PLAY_MINECRAFT, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_COMMENT_ON_USER_EXPERIENCE_AND_ASK_IF_USER_WANTS_TO_KNOW_HOW_TO,
    {
        MinecraftState.SYS_USER_WANTS_TO_KNOW_HOW_TO: user_says_yes_request,
        MinecraftState.SYS_USER_DOESNT_WANT_TO_KNOW_HOW_TO: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_COMMENT_ON_USER_EXPERIENCE_AND_ASK_IF_USER_WANTS_TO_KNOW_HOW_TO, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_TELLS_WHEN_HE_STARTED_TO_PLAY_MINECRAFT_AND_NO_HOW_TOS_LEFT,
    MinecraftState.USR_COMMENT_ON_USER_EXPERIENCE_AND_SAY_BUILD_HOGWARTS_PHRASE,
    minecraft_nlg.comment_on_user_experience_and_say_build_hogwarts_phrase,
)
simplified_dialogflow.set_error_successor(
    MinecraftState.SYS_USER_TELLS_WHEN_HE_STARTED_TO_PLAY_MINECRAFT_AND_NO_HOW_TOS_LEFT, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_WANTS_TO_KNOW_HOW_TO,
    MinecraftState.USR_TELL_HOW_TO_AND_ASK_USER_IF_IT_WAS_INTERESTING,
    minecraft_nlg.tell_how_to_and_ask_if_it_was_interesting_response,
)
simplified_dialogflow.set_error_successor(MinecraftState.SYS_USER_WANTS_TO_KNOW_HOW_TO, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_TELL_HOW_TO_AND_ASK_USER_IF_IT_WAS_INTERESTING,
    {
        MinecraftState.SYS_BOT_WILL_GIVE_ANOTHER_HOW_TO: minecraft_intents.bot_will_give_another_how_to_request,
        MinecraftState.SYS_BOT_CANNOT_GIVE_MORE_HOW_TOS: minecraft_intents.bot_cannot_give_more_how_tos_request,
    },
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_TELL_HOW_TO_AND_ASK_USER_IF_IT_WAS_INTERESTING, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_BOT_CANNOT_GIVE_MORE_HOW_TOS,
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    partial(
        minecraft_nlg.tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response,
        must_continue=False,
        prefix="It's probably boring to listen to long instructions.",
    ),
)
simplified_dialogflow.set_error_successor(MinecraftState.SYS_BOT_CANNOT_GIVE_MORE_HOW_TOS, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_BOT_WILL_GIVE_ANOTHER_HOW_TO,
    MinecraftState.USR_ASK_IF_USER_WANTS_TO_KNOW_HOW_TO,
    partial(
        minecraft_nlg.ask_if_user_wants_to_know_how_to_response,
        must_continue=False,
    ),
)
simplified_dialogflow.set_error_successor(MinecraftState.SYS_BOT_WILL_GIVE_ANOTHER_HOW_TO, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_ASK_IF_USER_WANTS_TO_KNOW_HOW_TO,
    {
        MinecraftState.SYS_USER_WANTS_TO_KNOW_HOW_TO: user_says_yes_request,
        MinecraftState.SYS_USER_DOESNT_WANT_TO_KNOW_HOW_TO: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(MinecraftState.USR_ASK_IF_USER_WANTS_TO_KNOW_HOW_TO, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_DOESNT_WANT_TO_KNOW_HOW_TO,
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    partial(
        minecraft_nlg.tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response,
        must_continue=False,
        prefix="Okay.",
    ),
)
simplified_dialogflow.set_error_successor(MinecraftState.SYS_USER_DOESNT_WANT_TO_KNOW_HOW_TO, MinecraftState.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    {MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT: user_says_anything_request},
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    MinecraftState.USR_COMMENT_ON_USER_EXPERIENCE_AND_SAY_BUILD_HOGWARTS_PHRASE,
    {MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT: user_says_anything_request},
)
simplified_dialogflow.set_error_successor(
    MinecraftState.USR_COMMENT_ON_USER_EXPERIENCE_AND_SAY_BUILD_HOGWARTS_PHRASE, MinecraftState.SYS_ERR
)
##############################################################
simplified_dialogflow.add_system_transition(
    MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT,
    (scopes.MAIN, scopes.State.USR_ROOT),
    minecraft_nlg.praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response,
)
simplified_dialogflow.set_error_successor(
    MinecraftState.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT, MinecraftState.SYS_ERR
)
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
