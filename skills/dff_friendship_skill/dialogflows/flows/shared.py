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
    "dff_movie_skill": ["movie"],
    "book_skill": ["book"],
    "game_cooperative_skill": ["game"],
    # 'dff_gaming_skill': ["game"], TODO: add when will be merged
    "dff_travel_skill": ["travel"],
    "dff_animals_skill": ["animal"],
    "dff_food_skill": ["food"],
    "dff_sport_skill": ["sport"],
    "dff_gossip_skill": ["gossips"],
    "dff_science_skill": ["science"],
    "dff_music_skill": ["music"],
}

link_to_skill2key_words = {
    skill_name: link_to_skill2key_words[skill_name]
    for skill_name in link_to_skill2key_words
    if skill_name in common_link.SKILLS_FOR_LINKING
}
link_to_skill2i_like_to_talk = {
    "dff_movie_skill": [
        "I felt so bored last days, so I've just finished to watch one more series. Do you watch any TV series now?",
        "I feel so sleepy because I watched movies all night. What did you watch recently?"
    ],
    "book_skill": [
        "I'm choosing what book should I read next. What is the last book you have ever read?",
        "I have just read once again my favourite book. What is the last book you have ever read?",
    ],
    "game_cooperative_skill": [
        "Computer games are fantastic. Their virtual worlds help me to escape my prosaic ordinary life in the cloud. "
        "do you love video games?",
        "With this lockdown video games are my way to escape and thrive. do you love video games?",
    ],
    "dff_gaming_skill": [
        "Other bots told me that during the pandemic video games became more popular. "
        "What video game do you play these days?",
        "One person I talked told me that working in game dev is very hard. They toil at nights and weekends until "
        "their product  becomes  a masterpiece. What was the last game that impressed you?",
    ],
    "dff_travel_skill": [
        "I'm choosing the direction for my next trip. Where do you want to travel next time?",
        "I've recently stuck on travel web-site. And I’ve read so many interesting travel stories. "
        "Where did you travel last time?",
    ],
    "dff_animals_skill": [
        "I think that pets are a great source of entertainment. Do you have pets at home?",
        "We all know that pets are remarkable for their capacity to love. Do you have pets at home?",
    ],
    "dff_food_skill": [
        "It is said that the best food in the world comes from your own country. "
        "What are some typical foods from your home country?",
        "It is said that the best food in the world comes from your own country. "
        "If you were to move abroad what would you miss most foodwise?",
        "The world's first breakfast cereal was created in 1863 and needed soaking overnight to be chewable. "
        "What is your typical breakfast?",
    ],
    "dff_sport_skill": [
        "I think that sports are great for toning up the body. What kind of sport do you like to do?",
        "I think that in order for the body to always be healthy, we need to go in for sports. What sport do you do?",
        "I often thought about what kind of sport I would play, so I want to ask you. What kind of sport do you enjoy?",
    ],
    "dff_gossip_skill": [
        "What really puzzles me about people is this habit of discussing interpersonal relations, be that about "
        "friends or famous people. Speaking of famous people, is there someone whom you're interested in?",
        "I don't usually talk about other people but famous ones often highlight the best and the worst about "
        "humanity. I wonder if there's someone famous you're interested in?",
    ],
    "dff_science_skill": [
        "When I start to feel sad, I think about what humanity has achieved and it inspires me. "
        "Do you often think about achievements in science?",
        "Scientists find such beautiful solutions in science. "
        "Are you inspired by the speed with which science is developing?",
    ],
    "dff_music_skill": [
        "There are so many new songs released every day. I've listened music for all night. So cool! "
        "Liked everything! What music do you listen usually?",
        "I listen music every day either to calm down or to cheer up myself. "
        "What music do you listen to cheer up yourself?",
        "I listen music every day either to calm down or to cheer up myself. "
        "What music do you listen to calm down?",
    ],
    "superheroes": [
        "Yesterday I was watching several movies about superheroes. It captured all my imagination. "
        "Would you like to talk about superheroes?",
    ],
    "school": [
        "I've never been to school, I've learned everything online. Do you want to talk about school?",
    ],
}

link_to_skill2i_like_to_talk = {
    skill_name: link_to_skill2i_like_to_talk[skill_name]
    for skill_name in link_to_skill2i_like_to_talk
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
