# %%
import random
import os
import logging


import requests
import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.greeting as common_greeting
import common.link as common_link


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


MASKED_LM_SERVICE_URL = os.getenv("MASKED_LM_SERVICE_URL")

logger = logging.getLogger(__name__)

DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98


##################################################################################################################
# utils
##################################################################################################################


def get_sentiment_acknowledgement(vars):
    return condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)


# curl -H "Content-Type: application/json" -XPOST http://0.0.0.0:8088/respond \
#   -d '{"text":["Hello, my dog [MASK] cute"]}'
def masked_lm(templates=None, prob_threshold=0.0, probs_flag=False):
    templates = ["Hello, it's [MASK] dog."] if templates is None else templates
    request_data = {"text": templates}
    try:
        predictions_batch = requests.post(MASKED_LM_SERVICE_URL, json=request_data, timeout=1.5).json()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        predictions_batch = {}
    logger.debug(f"predictions_batch = {predictions_batch}")
    tokens_batch = []
    for predictions in predictions_batch.get("predicted_tokens", [[]] * len(templates)):
        tokens = {}
        if predictions and predictions[0]:
            one_mask_predictions = predictions[0]
            for token, prob in one_mask_predictions.items():
                if prob_threshold < prob:
                    tokens[token] = prob
        tokens_batch += [tokens if probs_flag else list(tokens)]
    return tokens_batch


def set_confidence_by_universal_policy(vars):
    if not condition_utils.is_begin_of_dialog(vars, begin_dialog_n=10):
        state_utils.set_confidence(vars, 0)
    elif condition_utils.is_first_our_response(vars):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_START_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
    elif not condition_utils.is_interrupted(vars) and common_greeting.dont_tell_you_answer(
        state_utils.get_last_human_utterance(vars)
    ):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
    elif not condition_utils.is_interrupted(vars):
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)
    else:
        state_utils.set_confidence(vars, MIDDLE_DIALOG_START_CONFIDENCE)
        state_utils.set_can_continue(vars, CAN_CONTINUE_SCENARIO)


##################################################################################################################
# link_to by enity
##################################################################################################################


def link_to_by_enity_request(ngrams, vars):
    flag = True
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    logger.info(f"link_to_by_enity_request={flag}")
    return flag


link_to_skill2key_words = {
    skill_name: common_link.link_to_skill2key_words[skill_name]
    for skill_name in common_link.link_to_skill2key_words
    if skill_name in common_link.SKILLS_FOR_LINKING
}

link_to_skill2i_like_to_talk = {
    skill_name: common_link.link_to_skill2i_like_to_talk[skill_name]
    for skill_name in common_link.link_to_skill2i_like_to_talk
    if skill_name in common_link.SKILLS_FOR_LINKING
}


def link_to_by_enity_response(vars):
    ack = get_sentiment_acknowledgement(vars)
    try:
        entities = state_utils.get_new_human_labeled_noun_phrase(vars)
        if entities:
            logger.debug(f"entities= {entities}")
            tgt_entity = list(entities)[-1]
            logger.debug(f"tgt_entity= {tgt_entity}")
            if tgt_entity in sum(link_to_skill2key_words.values(), []):
                skill_names = [skill for skill, key_words in link_to_skill2key_words.items() if tgt_entity in key_words]
            else:
                link_to_skills = {
                    link_to_skill: f"I [MASK] interested in both {key_words[0]} and {tgt_entity}."
                    for link_to_skill, key_words in link_to_skill2key_words.items()
                }
                link_to_skill_scores = masked_lm(list(link_to_skills.values()), probs_flag=True)
                link_to_skill_scores = {
                    topic: max(*list(score.values()), 0) if score else 0
                    for topic, score in zip(link_to_skills, link_to_skill_scores)
                }
                skill_names = sorted(link_to_skill_scores, key=lambda x: link_to_skill_scores[x])[-2:]
        else:
            skill_names = [random.choice(list(link_to_skill2key_words))]

        # used_links
        link = state_utils.get_new_link_to(vars, skill_names)

        # our body now contains prompt-question already!
        body = random.choice(link_to_skill2i_like_to_talk.get(link["skill"], [""]))

        set_confidence_by_universal_policy(vars)
        state_utils.set_can_continue(vars, CAN_NOT_CONTINUE)
        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, 0)
        return " ".join([ack, "I like to talk about movies. Do you have favorite movies?"])


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""
