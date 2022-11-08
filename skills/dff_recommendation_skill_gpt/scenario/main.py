import logging
import re

import common.constants as common_constants
import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.utils as common_utils
import df_engine.conditions as cnd
import df_engine.labels as lbl
from df_engine.core import Actor, Context
from df_engine.core.keywords import (GLOBAL, LOCAL, PROCESSING, RESPONSE, TRANSITIONS)
from goal_dialogpt_skill import GET_RECOMMENDATION_PATTERN, CHAT_ABOUT_EXPLICIT

from . import condition as loc_cnd
from . import processing as loc_prs
from . import response as loc_rsp

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
            ("give_recommendation", "ask_for_details", 1.1): cnd.regexp(GET_RECOMMENDATION_PATTERN), #потом поставить нормальные человеческие конфиденсы
            ("ask_about", "begin", 1.1): loc_cnd.bot_takes_initiative, #проверить почему там 5 а не 3 НЕ РАБОТАЕТ
            ("chat_about", "start_topic", 1.1): cnd.regexp(CHAT_ABOUT_EXPLICIT), 
            ("ask_about", "begin", 1.1): loc_cnd.short_thank_you
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("give_recommendation", "ask_for_details"): cnd.regexp(GET_RECOMMENDATION_PATTERN),
                #("ask_about", "begin"): loc_cnd.bot_takes_initiative, #проверить почему там 5 а не 3
                ("chat_about", "begin"): cnd.regexp(CHAT_ABOUT_EXPLICIT), 
                ("greeting", "begin"): cnd.true()
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
            "Any details?", "All right. Please, tell me more about what you want.", 
            "I'd love to help! Please, give me more details on what you want."]),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps("request"),
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
            RESPONSE: loc_rsp.generative_response(recommend=True, discussed_entity="request"),
            PROCESSING: {
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN), 
                "ask_for_approval": cnd.true(),
            },
        },
        "details_given": {
            RESPONSE: loc_rsp.generative_response(recommend=True, discussed_entity="request"),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps("details")
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
            RESPONSE: int_rsp.multi_response(replies=[
                "So are you gonna try this one?",
                "What do you think about it?"
                "So what do you think about this one?", 
                "Do you like my suggestion?",
                "So what do you think?"
                ]),
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
            RESPONSE: int_rsp.multi_response(replies=[
                "Oh, and I have more things in mind, do you want to discuss them? ",
                "Great! And I have more ideas, do you wanna hear them? ",
                "Happy to help. By the way, I have some other ideas! Do you want to hear me out? ",
                ]),
            TRANSITIONS: {
                "second_recommendation": int_cnd.is_yes_vars,
                ("ask_about", "begin"): cnd.true()
                },
        },
        "user_discontented": {
            RESPONSE: int_rsp.multi_response(replies=[
                "Let me try again! I'll do my best.",
                "Oh, I'm not a wizard, I'm still learning... But I can try again!",
                "Let's give it another try, shall we?"
            ]),
            TRANSITIONS: {
                ("ask_about", "begin"): int_cnd.is_no_vars,
                "second_recommendation": cnd.true()
                },
        },
        "second_recommendation": { #как контекст использовать ТОЛЬКО реквест а ой уже вроде сделала, проверить
            RESPONSE: loc_rsp.generative_response(recommend=True, discussed_entity="request"),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                ("ask_about", "begin"): cnd.true()},
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
            RESPONSE: loc_rsp.ask_about_presequence_2, #возможно вложить в прошлую функцию
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
                "give_bots_opinion_entity": loc_cnd.contains_noun_phrase,
            },
        },
        "give_bots_opinion_entity": {
            RESPONSE: loc_rsp.generative_response(),  
            PROCESSING: {
                "save_previous_utterance_nps": loc_prs.save_previous_utterance_nps('topic_entity')
                },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                ("chat_about", "start_topic"): cnd.true()
            },
        },
        "answer_question": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                ("chat_about", "start_topic"): cnd.true()
                },
        },
        "give_opinion": {
            RESPONSE: loc_rsp.generative_response(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                ("chat_about", "start_topic"): cnd.true()
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
        "begin": { # convers-evaluation-selector: docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/proxy.yml logs -f dff-recommendation-skill-gpt 0 
            RESPONSE: int_rsp.multi_response(replies=["Hey there, it's DREAM! I can recommend you something interesting, answer your questions or just chat with you. How are you doing?", 
            "Hey there, it's DREAM! I can recommend you something interesting, answer your questions or just chat with you. How is it going?",
            "Hey there, it's DREAM! I can recommend you something interesting, answer your questions or just chat with you. How are you feeling?"]),  # several hypothesis
            PROCESSING: {
            },
            TRANSITIONS: {"second_utt": cnd.true(),
            },
        },
        "second_utt": {
            RESPONSE: loc_rsp.generate_with_string(to_append=['What are you up to today?', 'What are your plans for today?',
            'Any special plans for today?'], position_string='before'),  #не учитываются вопросы
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('discussed_entity') 
            },
            TRANSITIONS: {
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": loc_cnd.is_slot_filled,
                "third_utt": cnd.true(),
            },
        },
        "third_utt": {
            RESPONSE: loc_rsp.generate_with_string(to_append="By the way, I am so hungry... What is your favourite dish?", position_string='before'),
            TRANSITIONS: {
                "continue_discussing_entity": cnd.true(),
            },
        },
        "continue_discussing_entity": { 
            RESPONSE: loc_rsp.generative_response(discussed_entity='discussed_entity'), 
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('discussed_entity')
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
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('discussed_entity')
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
            },
            TRANSITIONS: {
                "react_name": loc_cnd.contains_named_entities,
                ("chat_about", "begin"): cnd.true()
                },
        },
        "react_name": { # проверить чтоб у нас не лежало имя посмотреть personal info skill (если добавляем то это более-менее бесполезно тк нас перебьет персонлинфо скилл)
            RESPONSE: "Nice to meet you, {user_name}. What do you want to chat about?", #нужно сделать свой дфф-форматтер (добавить возвр. имени),  написать денису спросить как получить доступ к диалоговому стейту
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_user_name(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                ("chat_about", "start_topic"): loc_cnd.contains_noun_phrase,
                ("ask_about", "begin"): cnd.true()
                },
        },
    },
    "chat_about": { 
        LOCAL: {
            PROCESSING: {
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
                "start_topic": cnd.true()
            },
        },
        "user_ignores_question": {
            RESPONSE: loc_rsp.generative_response(),  
            TRANSITIONS: {
                "answer_question": cnd.any(
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
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('topic_entity')
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
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('discussed_entity')
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
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('discussed_new_entity')
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
                "save_slots_to_ctx": loc_prs.save_previous_utterance_nps('discussed_entity')
            },
            TRANSITIONS: {
                "give_hyponym_definition": cnd.all([
                    cnd.any(
                [int_cnd.is_no_vars, 
                int_cnd.is_do_not_know_vars,
                loc_cnd.what_is_question #не отрабатывает это условие, видимо из-за доставания из контекста.
                ]
                ),
                loc_cnd.we_have_hyp_def]),
                # cnd.all([cnd.any(
                # [int_cnd.is_no_vars, 
                # int_cnd.is_do_not_know_vars,
                # loc_cnd.what_is_question
                # ]),
                # loc_cnd.is_hyponym
                # ]
                # ),
                "answer_question": int_cnd.is_question, 
                "new_entity": loc_cnd.contains_noun_phrase,
                "continue_discussing_entity": cnd.true(),
            },
        },
        "give_hyponym_definition":{
            RESPONSE: loc_rsp.give_hyponym_definition(),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
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
