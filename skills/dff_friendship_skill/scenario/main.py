import logging

import common.dff.integration.processing as int_prs
import scenario.condition as loc_cnd
import scenario.response as loc_rsp
import scenario.weekend_condition as loc_wkd_cnd
import scenario.weekend_response as loc_wkd_rsp
from common.constants import CAN_NOT_CONTINUE
from df_engine.core.keywords import PROCESSING, TRANSITIONS, RESPONSE
from df_engine.core import Actor


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)
ZERO_CONFIDENCE = 0.0

flows = {
    "global_flow": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("greeting_flow", "false_positive_node"): loc_cnd.false_positive_condition,
                ("greeting_flow", "hello_response_node"): loc_cnd.hello_condition,
                ("greeting_flow", "how_are_you_node"): loc_cnd.how_are_you_condition,
                ("greeting_flow", "std_greeting_node"): loc_cnd.std_greeting_condition,
                ("greeting_flow", "new_entities_is_needed_for_node"): loc_cnd.new_entities_is_needed_for_condition,
                ("greeting_flow", "link_to_by_enity_node"): loc_cnd.link_to_by_enity_condition,
                ("weekend_flow", "std_weekend_node"): loc_wkd_cnd.std_weekend_condition,
            },
        },
        "fallback": {
            RESPONSE: "Sorry",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_NOT_CONTINUE),
            },
        },
    },
    "greeting_flow": {
        "false_positive_node": {
            RESPONSE: loc_rsp.false_positive_response,
            TRANSITIONS: {
                "hello_response_node": loc_cnd.not_is_no_condition,
                "bye_response_node": loc_cnd.is_no_condition,
            },
        },
        "bye_response_node": {
            RESPONSE: loc_rsp.bye_response,
            TRANSITIONS: {},
        },
        "hello_response_node": {
            RESPONSE: loc_rsp.greeting_response,
            TRANSITIONS: {
                "how_are_you_node": loc_cnd.how_are_you_condition,
                "how_human_is_doing_node": loc_cnd.no_requests_condition,
                ("weekend_flow", "std_weekend_node"): loc_wkd_cnd.std_weekend_condition,
            },
        },
        "how_are_you_node": {
            RESPONSE: loc_rsp.how_are_you_response,
            TRANSITIONS: {
                "std_greeting_node": loc_cnd.std_greeting_condition,
            },
        },
        "how_human_is_doing_node": {
            RESPONSE: loc_rsp.how_human_is_doing_response,
            TRANSITIONS: {
                "std_greeting_node": loc_cnd.std_greeting_condition,
            },
        },
        "std_greeting_node": {
            RESPONSE: loc_rsp.std_greeting_response,
            TRANSITIONS: {
                "offered_topic_choice_declined_node": loc_cnd.offered_topic_choice_declined_condition,
                "asked_for_events_and_got_yes_node": loc_cnd.asked_for_events_and_got_yes_condition,
                "std_greeting_node": loc_cnd.std_greeting_condition,
            },
        },
        "offered_topic_choice_declined_node": {
            RESPONSE: loc_rsp.offered_topic_choice_declined_response,
            TRANSITIONS: {
                "std_greeting_node": loc_cnd.std_greeting_condition,
            },
        },
        "asked_for_events_and_got_yes_node": {
            RESPONSE: loc_rsp.clarify_event_response,
            TRANSITIONS: {
                "std_greeting_node": loc_cnd.std_greeting_condition,
            },
        },
        "new_entities_is_needed_for_node": {
            RESPONSE: loc_rsp.closed_answer_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "link_to_by_enity_node": {
            RESPONSE: loc_rsp.link_to_by_enity_response,
            TRANSITIONS: {
                "std_greeting_node": loc_cnd.std_greeting_condition,
            },
        },
    },
    "weekend_flow": {
        "std_weekend_node": {
            RESPONSE: loc_wkd_rsp.std_weekend_response,
            TRANSITIONS: {
                "sys_cleaned_up_node": loc_wkd_cnd.sys_cleaned_up_condition,
                "sys_slept_in_node": loc_wkd_cnd.sys_slept_in_condition,
                "sys_read_book_node": loc_wkd_cnd.sys_read_book_condition,
                "sys_watched_film_node": loc_wkd_cnd.sys_watched_film_condition,
                "sys_played_computer_game_node": loc_wkd_cnd.sys_played_computer_game_condition,
            },
        },
        "sys_cleaned_up_node": {
            RESPONSE: loc_wkd_rsp.sys_cleaned_up_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "sys_slept_in_node": {
            RESPONSE: loc_wkd_rsp.sys_slept_in_response,
            TRANSITIONS: {
                "sys_feel_great_node": loc_wkd_cnd.sys_feel_great_condition,
                "sys_need_more_time_node": loc_wkd_cnd.sys_need_more_time_condition,
            },
        },
        "sys_feel_great_node": {
            RESPONSE: loc_wkd_rsp.sys_feel_great_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "sys_need_more_time_node": {
            RESPONSE: loc_wkd_rsp.sys_need_more_time_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "sys_read_book_node": {
            RESPONSE: loc_wkd_rsp.sys_read_book_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "sys_watched_film_node": {
            RESPONSE: loc_wkd_rsp.sys_watched_film_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "sys_played_computer_game_node": {
            RESPONSE: loc_wkd_rsp.sys_played_computer_game_response,
            TRANSITIONS: {
                "sys_play_on_weekends_node": loc_wkd_cnd.sys_play_on_weekends_condition,
            },
        },
        "sys_play_on_weekends_node": {
            RESPONSE: loc_wkd_rsp.sys_play_on_weekends_response,
            TRANSITIONS: {
                "sys_play_regularly_node": loc_wkd_cnd.sys_play_regularly_condition,
                "sys_play_once_node": loc_wkd_cnd.sys_play_once_condition,
            },
        },
        "sys_play_regularly_node": {
            RESPONSE: loc_wkd_rsp.sys_play_regularly_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "sys_play_once_node": {
            RESPONSE: loc_wkd_rsp.sys_play_once_response,
            TRANSITIONS: {
                "link_to_by_enity_node": loc_cnd.link_to_by_enity_condition,
            },
        },
        "link_to_by_enity_node": {
            RESPONSE: loc_rsp.link_to_by_enity_response,
            TRANSITIONS: {
                "std_weekend_node": loc_wkd_cnd.std_weekend_condition,
            },
        },
    },
}

actor = Actor(
    flows,
    start_label=("global_flow", "start"),
    fallback_label=("global_flow", "fallback"),
)
logger.info("Actor created successfully")
