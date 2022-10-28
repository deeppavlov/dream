import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor, Context
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.dff.integration.context as int_ctx

import common.utils as common_utils
import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp
from . import processing as loc_prs

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from df_engine.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

THANK_PATTERN = re.compile(r"thanks|thank you|(I'll|I will) (try|watch|read|cook|think)|okay|good|great", re.IGNORECASE)


flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("give_recommendation", "begin"): cnd.regexp(r"give recommendation flow", re.IGNORECASE),
            ("ask_about", "begin"): cnd.regexp(r"ask about flow", re.IGNORECASE),
            ("greeting", "begin"): cnd.regexp(r"greeting flow", re.IGNORECASE),
            ("chat_about", "begin"): cnd.regexp(r"chat about flow", re.IGNORECASE)
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("give_recommendation", "begin"): cnd.regexp(r"give recommendation flow", re.IGNORECASE),
                ("ask_about", "begin"): cnd.regexp(r"ask about flow", re.IGNORECASE),
                ("greeting", "begin"): cnd.regexp(r"greeting flow", re.IGNORECASE),
                ("chat_about", "begin"): cnd.regexp(r"chat about flow", re.IGNORECASE)
                },
        },
        "fallback": {
            RESPONSE: "Ooops",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "give_recommendation": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "begin": {
            RESPONSE: "I'm here to recommend you something nice.", 
            TRANSITIONS: {"ask_for_details": cnd.true()
            },
        },
        "ask_for_details": {
            RESPONSE: int_rsp.multi_response(replies=["Could you give me some more details on what you want?", 
            "Any details?"]),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance("request")
            },
            TRANSITIONS: {"details_denied": cnd.any(
                [int_cnd.is_no_vars, 
                int_cnd.is_do_not_know_vars,
                loc_cnd.is_negative_sentiment
                ],
                ),
                "details_given": cnd.true()
            },
        },
        "details_denied": {
            RESPONSE: loc_rsp.generative_response(recommend=True),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance("")
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN), 
                "ask_for_approval": cnd.true(),
            },
        },
        "details_given": {
            RESPONSE: loc_rsp.generative_response(recommend=True),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance("details")
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),
                "ask_for_approval": cnd.true(),
            },
        },
        "answer_question": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),
                "ask_for_approval": cnd.true()
                },
        },
        "give_opinion": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),
                "ask_for_approval": cnd.true()
                },
        },
        "ask_for_approval": {
            RESPONSE: int_rsp.multi_response(replies=["So are you gonna try this one out?",
            "What do you think about it?"
            "So what do you think about my recommendation?", 
            "Do you like my suggestion?"]),
            TRANSITIONS: {
                "user_discontented": cnd.any(
                [int_cnd.is_no_vars, 
                int_cnd.is_do_not_know_vars,
                loc_cnd.is_negative_sentiment
                ],
                ),
                "user_contented": cnd.true()
                },
        },
        "user_contented": {
            RESPONSE: "Happy to help. By the way, I have some other ideas! Do you want to hear me out?",
            TRANSITIONS: {
                "second_recommendation": int_cnd.is_yes_vars,
                "finish": cnd.true()
                },
        },
        "user_discontented": {
            RESPONSE: int_rsp.multi_response(replies=["Let me try again! I'll do my best.",
            "Oh, I'm not a wizard, I'm still learning... But I have another idea!"]),
            TRANSITIONS: {
                "finish": int_cnd.is_no_vars,
                "second_recommendation": cnd.true()
                },
        },
        "second_recommendation": { 
            RESPONSE: loc_rsp.generative_response(recommend=True, discussed_entity="request"),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "finish": cnd.true()},
        },
        "finish": {
            RESPONSE: "Okay, have fun.",
            TRANSITIONS: {},
        },
    },
    "ask_about": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "begin": {
            RESPONSE: loc_rsp.ask_about_presequence, 
            TRANSITIONS: {
                "user_ignores_question": cnd.any(
                    [
                    int_cnd.is_question, 
                    int_cnd.is_opinion_request
                    ]
                ),
                "begin": cnd.any(
                    [
                    int_cnd.is_no_vars, 
                    int_cnd.is_do_not_know_vars,
                    loc_cnd.is_negative_sentiment
                    ],
                ),
                "likes_topic": cnd.true()
            },
        },
        "user_ignores_question": {
            RESPONSE: loc_rsp.ask_about_presequence_2, 
            TRANSITIONS: {
                "begin": cnd.any(
                    [
                    int_cnd.is_no_vars, 
                    int_cnd.is_do_not_know_vars,
                    loc_cnd.is_negative_sentiment,
                    int_cnd.is_question, 
                    int_cnd.is_opinion_request
                    ],
                ),
                "likes_topic": cnd.true()
            },
        },
        "likes_topic": {
            RESPONSE: loc_rsp.generate_with_string(), 
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "give_bots_opinion_entity": cnd.true()
            },
        },
        "give_bots_opinion_entity": {
            RESPONSE: loc_rsp.generative_response(),  
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                ("give_recommendation", "finish"): cnd.true()
            },
        },
        "answer_question": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                },
        },
        "give_opinion": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                },
        },
    },
    "greeting": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0), #убрать их отовсюду где нужны разветвления, оба, и сет_конфиденс делать внутри респонс-файла, прям там где мы генерим респонс давать разный конфиденс в зависимости от условий
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "begin": { # convers-evaluation-selector: GREETING-FIRST = 0 
            RESPONSE: int_rsp.multi_response(replies=["Hey there, it's DREAM! I can recommend you something interesting, answer your questions or just chat with you. How are you doing?", 
            "Hey there, it's DREAM! I can recommend you something interesting, answer your questions or just chat with you. How is it going?",
            "Hey there, it's DREAM! I can recommend you something interesting, answer your questions or just chat with you. How are you feeling?"]),  # several hypothesis
            PROCESSING: {
            },
            TRANSITIONS: {"second_utt": cnd.true(),
            },
        },
        "second_utt": {
            RESPONSE: loc_rsp.generate_np_response(response_options=['What are you up to today?', 'What are your plans for today?',
            'Any special plans for today?']), 
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('discussed_entity') 
            },
            TRANSITIONS: {
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": loc_cnd.is_slot_filled,
                "third_utt": cnd.true(),
            },
        },
        "third_utt": {
            RESPONSE: loc_rsp.generate_np_response(response_options=["""By the way, what is your favourite dish?"""]),  
            TRANSITIONS: {
                "continue_discussing_entity": cnd.true(),
            },
        },
        "continue_discussing_entity": { 
            RESPONSE: loc_rsp.generative_response(discussed_entity='discussed_entity'), 
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('discussed_entity')
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "ask_name": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "new_entity": {
            RESPONSE: loc_rsp.generative_response(discussed_entity='discussed_entity'),  
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('discussed_entity')
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "ask_name": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "answer_question": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "ask_name": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
                },
        },
        "give_opinion": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "ask_name": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
                },
        },
        "ask_name": { # проверить чтоб у нас не лежало имя посмотреть personal info skill
            RESPONSE: int_rsp.multi_response(replies=["Oh, I still don't your name! What should I call you?", 
            "By the way, what is your name, if I may ask?", "Now that we know each other better, may I ask your name?"]),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('test')
            },
            TRANSITIONS: {
                "react_name": cnd.true()
                },
        },
        "react_name": { # проверить чтоб у нас не лежало имя посмотреть personal info skill (если добавляем то это более-менее бесполезно тк нас перебьет персонлинфо скилл)
            RESPONSE: 'Nice to meet you, {test}', #нужно сделать свой дфф-форматтер (добавить возвр. имени),  написать денису спросить как получить доступ к диалоговому стейту
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                },
        },
    },
    "chat_about": { 
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            
            },
        },
        "begin": {
            RESPONSE: 'What do you want to chat about today?',  #pre-question
            TRANSITIONS: {
                "user_ignores_question": cnd.any(
                    [
                    int_cnd.is_question, 
                    int_cnd.is_opinion_request
                    ]
                ),
                "start_topic": loc_cnd.contains_noun_phrase
            },
        },
        "user_ignores_question": {
            RESPONSE: loc_rsp.generative_response(),  
            TRANSITIONS: {
                "user_ignores_question": cnd.any(
                    [
                    int_cnd.is_question, 
                    int_cnd.is_opinion_request
                    ]
                ),
                "start_topic": cnd.true()
            },
        },
        "start_topic": { 
            RESPONSE: loc_rsp.generative_response(discussed_entity='topic_entity'),  
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('topic_entity')
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "ask_hyponym_question": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "continue_discussing_entity": { 
            RESPONSE: loc_rsp.generative_response(discussed_entity='discussed_entity'), 
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('discussed_entity')
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "ask_hyponym_question": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "new_entity": {
            RESPONSE: loc_rsp.generative_response(discussed_entity='discussed_entity'),  # several hypothesis
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('discussed_new_entity')
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "ask_hyponym_question": loc_cnd.enough_generative_responses,
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "ask_hyponym_question": {
            RESPONSE: loc_rsp.generate_with_string(to_append='get_hyponyms'),  
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance('discussed_entity')
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "answer_question": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "ask_hyponym_question": loc_cnd.enough_generative_responses,
                "continue_discussing_entity": cnd.true(),
                },
        },
        "give_opinion": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "ask_hyponym_question": loc_cnd.enough_generative_responses,
                "continue_discussing_entity": cnd.true(),
                },
        },
        "bye": {
            RESPONSE: 'end',
            TRANSITIONS: {},
        },
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))