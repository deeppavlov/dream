# %%
import os
import logging
import random
import re

import sentry_sdk

from collections import defaultdict
import spacy
import json

import nltk
from nltk import wordpunct_tokenize
from nltk import word_tokenize

import common.dialogflow_framework.utils.state as state_utils
import common.constants as common_constants

# from common.gossip import talk_about_gossip, skill_trigger_phrases

from common.speech_functions import utils as current_utils
from common.psychometrics import is_introvert

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)

# required for Generic Response function
nlp = spacy.load("en_core_web_sm")
nltk.download("punkt")

file = None

with open("common/speech_functions/res_cor.json") as data:
    file = json.load(data)

# region Sample Data

dialogues = []
if file:
    for d in file[:2]:
        samples = defaultdict(dict)
        result = d["completions"][0]["result"]
        texts_without_labels = d["data"]["text"]
        for sample in result:
            speaker = texts_without_labels[int(sample["value"]["start"])]["speaker"]
            samples[sample["id"]]["speaker"] = speaker
            samples[sample["id"]]["text"] = sample["value"]["text"]
            samples[sample["id"]]["start"] = int(sample["value"]["start"])
            if "paragraphlabels" in sample["value"]:
                samples[sample["id"]]["paragraphlabels"] = sample["value"]["paragraphlabels"][0]
            if "choices" in sample["value"]:
                samples[sample["id"]]["choices"] = sample["value"]["choices"][0]

        sorted_samples = sorted([(samples[sample_id]["start"], sample_id) for sample_id in samples])
        texts = []
        labels = []
        speakers = []
        for _, sample_id in sorted_samples:
            if samples[sample_id]["text"] != "PAUSE":
                texts.append(str(samples[sample_id]["text"]).replace("\n", ""))
                speakers.append(samples[sample_id]["speaker"])
                paragraph_labels = samples[sample_id].get("paragraphlabels", "")
                choices = samples[sample_id].get("choices", "")
                labels.append(paragraph_labels + "." + choices)
        dialogues.append((texts, labels, speakers))

    train_data = dialogues[1][0]
    test_data = dialogues[0][0]
    all_data = train_data + test_data

    train_labels = dialogues[1][1]
    test_labels = dialogues[0][1]
    all_labels = train_labels + test_labels

registers = []
if file:
    for i in zip(all_data, all_labels):
        if "Register" in i[1]:
            if len(wordpunct_tokenize(i[0])) < 3:
                if "Leah" not in i[0]:
                    if "shit" not in i[0]:
                        registers.append(i[0].strip("."))

registers = list(set(registers))

# endregion


# region CONFIDENCES
DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98

MUST_CONTINUE_CONFIDENCE = 0.98
CAN_CONTINUE_CONFIDENCE = 0.9
CANNOT_CONTINUE_CONFIDENCE = 0.0
# endregion

# endregion

################################################################################
# %%

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################
##################################################################################################################


# utils

patterns_supported_speech_functions = ["Register", "Check", "Confirm", "Monitor", "Affirm", "Agree", "Clarify"]

supported_speech_functions_patterns_re = re.compile(
    "(" + "|".join(patterns_supported_speech_functions) + ")", re.IGNORECASE
)


def is_supported_speech_function(human_utterance, bot_utterance):
    sf_functions = current_utils.get_speech_function_for_human_utterance(human_utterance)
    logger.info(f"Found Speech Function(s): {sf_functions}")

    sf_predictions = current_utils.get_speech_function_predictions_for_human_utterance(human_utterance)
    if sf_predictions:
        sf_predictions_list = list(sf_predictions)
        sf_predictions_for_last_phrase = sf_predictions_list[-1]

        for sf_predicted in sf_predictions_for_last_phrase:
            prediction = sf_predicted["prediction"]
            logger.info(f"prediction: {prediction}")
            supported = bool(re.search(supported_speech_functions_patterns_re, prediction))
            if supported:
                logger.info(
                    f"At least one of the proposed speech functions is supported "
                    f"for generic response: {sf_predicted}"
                )
                return True

    # Temporary Override
    return True


def get_pre_last_human_utterance(vars):
    return vars["agent"]["dialog"]["human_utterances"][-2]


def get_pre_last_bot_utterance(vars):
    return vars["agent"]["dialog"]["bot_utterances"][-2]


def is_last_bot_utterance_by_us(vars):
    bot_utterances = state_utils.get_bot_utterances(vars)
    if len(bot_utterances) == 0:
        return False

    last_bot_utterance = state_utils.get_last_bot_utterance(vars)

    active_skill = last_bot_utterance["active_skill"]

    if active_skill == "dff_generic_responses_skill":
        return True

    return False


##################################################################################################################
# Generic Response Function: Generates response based on the predicted Speech Function to a given user's phrase
# Author: Lida Ostyakova
##################################################################################################################

# sustain_monitor=['You know?', 'Alright?','Yeah?','See?','Right?']
# reply_agree=["Oh that's right. That's right.", "Yep.", "Right.", 'Sure', 'Indeed', 'I agree with you']
# reply_disagree=['No', 'Hunhunh.', "I don't agree with you", "I disagree", "I do not think so", "I hardly think so",
# "I can't agree with you"]
# reply_disawow=['I doubt it. I really do.', "I don't know.", "I'm not sure", 'Probably.', "I don't know if it's true"]
# reply_acknowledge=['I knew that.','I know.', 'No doubts', 'I know what you meant.', 'Oh yeah.','I see']
reply_affirm = [
    "Oh definitely.",
    "Yeah.",
    "Kind of.",
    "Unhunh",
    "Yeah I think so",
    "Really.",
    "Right.",
    "That's what it was.",
]
# reply_contradict=['Oh definitely no', 'No', 'No way', 'Absolutely not', 'Not at all', 'Nope', 'Not really', 'Hardly']
# # track_confirm=[' Oh really ?','Right ?', ' Okay ?']
# track_check=['Pardon?', 'I beg your pardon?', 'Mhm ?','Hm?','What do you mean?']


def clarify_response(previous_phrase):
    doc = nlp(previous_phrase)
    poses = []
    deps = []
    for token in doc:
        poses.append(token.pos_)
        deps.append(token.dep_)
        if token.pos_ == "NOUN" or token.pos_ == "PROPN":
            clarify_noun = token.text
            next_sent = "What " + clarify_noun + "?"
        elif token.dep_ == "prep":
            prep = token.text
            next_sent = str(prep).capitalize() + " what?"
        elif poses[0] == "PROPN" or poses[0] == "PRON":
            if word_tokenize(previous_phrase)[0].lower() == "i" or word_tokenize(previous_phrase)[0].lower() == "we":
                first_pron = "You"
                next_sent = first_pron + " what?"
            else:
                if word_tokenize(previous_phrase)[0].lower() != "what":
                    next_sent = word_tokenize(previous_phrase)[0] + " what?"
                else:
                    next_sent = "What?"
        else:
            next_sent = "What?"
    return next_sent


def confirm_response(previous_phrase):
    track_confirm = ["Oh really?", " Oh yeah?", "Sure?", "Are you sure?", "Are you serious?", "Yeah?"]
    if len(word_tokenize(previous_phrase)) > 5:
        next_sent = (word_tokenize(previous_phrase))[-1].capitalize() + "?"
    elif len(word_tokenize(previous_phrase)) < 4:
        if "you" in word_tokenize(previous_phrase):
            previous_phrase = re.sub("you", "me", previous_phrase)
        if "I " in previous_phrase:
            previous_phrase = re.sub("I", "you", previous_phrase)
        next_sent = previous_phrase + "?"
    else:
        next_sent = random.choice(track_confirm)
    return next_sent


def generate_response(vars, predicted_sf, previous_phrase, enable_repeats_register=False, user_name=""):
    response = None
    if "Register" in predicted_sf:
        response = random.choice(registers)
        if enable_repeats_register is True:
            response = word_tokenize(previous_phrase)[-1].capitalize() + "."
    if "Check" in predicted_sf:
        response = current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
        # response=random.choice(track_check)
    if "Confirm" in predicted_sf:
        response = confirm_response(previous_phrase)
    #     if 'Monitor' in predicted_sf:
    #         if user_name!='':
    #             response=user_name+', '+random.choice(sustain_monitor)
    #         else:
    #             response=current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
    # response = user_name+random.choice(sustain_monitor)  #можно добавить имя пользователя
    if "Affirm" in predicted_sf:
        response = current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
    #     if 'Disawow' in predicted_sf:
    #         response = current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
    #         # response=random.choice(reply_disawow)
    #     if 'Disagree' in predicted_sf:
    #         response = current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
    #         # response=random.choice(reply_disagree)
    if "Agree" in predicted_sf:
        response = current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
        # response=random.choice(reply_agree)
    #     if 'Contradict' in predicted_sf:
    #         response = current_utils.get_not_used_and_save_generic_response(predicted_sf, vars)
    # response=random.choice(reply_contradict)
    if "Clarify" in predicted_sf:
        response = clarify_response(previous_phrase)
    return response


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    logger.debug("exec error_response")
    state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
    state_utils.set_confidence(vars, 0)
    return ""


##################################################################################################################
# Handlers
##################################################################################################################


# region RESPONSE_TO_SPEECH_FUNCTION
##################################################################################################################


def sys_response_to_speech_function_request(vars):
    flag = False

    # added check for introvert/extravert
    try:
        dialog = state_utils.get_dialog(vars)
        human_uttr_idx = len(dialog["human_utterances"])

        logger.info(f"human dialog length: {human_uttr_idx}")

        if len(dialog["human_utterances"]) > 4:
            logger.info("human utterances number: at least 5")
            if is_introvert(dialog) is True:
                logger.info("user is: introvert")
                return False

            else:
                logger.info("user is: extravert")
                human_utterance = state_utils.get_last_human_utterance(vars)
                bot_utterance = state_utils.get_last_bot_utterance(vars)
                flag = is_supported_speech_function(human_utterance, bot_utterance)
                logger.info(f"sys_response_to_speech_function_request: {flag}")

    except Exception as exc:
        logger.exception(exc)
        logger.info(f"sys_response_to_speech_function_request: Exception: {exc}")
        sentry_sdk.capture_exception(exc)

    logger.info(f"sys_response_to_speech_function_request: {flag}")
    return flag


def usr_response_to_speech_function_response(vars):
    logger.debug("exec usr_response_to_speech_function_response")
    interrogative_words = ["whose", "what", "which", "who", "whom", "what", "which", "why", "where", "when", "how"]
    # aux_verbs = ['do', 'did', 'have', 'can', 'may', 'am', 'is', 'are', 'was', 'were']
    try:
        human_utterance = state_utils.get_last_human_utterance(vars)

        phrases = human_utterance["annotations"].get("sentseg", {}).get("segments", {})

        sf_functions = None

        cont = False

        if is_last_bot_utterance_by_us(vars) or len(word_tokenize(human_utterance["text"])) > 10:
            # check for "?" symbol in the standalone segments of the original user's utterance
            for phrase in phrases:
                if "?" not in phrase:
                    cont = True
                else:
                    cont = False
            if cont:
                sf_functions = current_utils.get_speech_function_for_human_utterance(human_utterance)
                logger.info(f"Found Speech Function: {sf_functions}")
            else:
                if word_tokenize(human_utterance["text"])[0] not in interrogative_words:
                    sf_functions = current_utils.get_speech_function_for_human_utterance(human_utterance)
                    logger.info(f"Found Speech Function: {sf_functions}")

        if not sf_functions:
            return error_response(vars)

        last_phrase_function = list(sf_functions)[-1]

        sf_predictions = current_utils.get_speech_function_predictions_for_human_utterance(human_utterance)
        logger.info(f"Proposed Speech Functions: {sf_predictions}")

        if not sf_predictions:
            return error_response(vars)

        generic_responses = []

        sf_predictions_list = list(sf_predictions)
        sf_predictions_for_last_phrase = sf_predictions_list[-1]

        for sf_prediction in sf_predictions_for_last_phrase:
            prediction = sf_prediction["prediction"]
            generic_response = generate_response(vars, prediction, last_phrase_function, False, "")
            if generic_response is not None:
                if generic_response != "??" and generic_response != ".?":
                    generic_responses.append(generic_response)

        # get ack, body
        # ack = ""
        # ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # generating response
        questions = [
            "Hi",
            "Hello",
            "Well hello there!",
            "Look what the cat dragged in!",
        ]  # common_gossip.TOPIC_TO_EVENT_QUESTIONS

        if not generic_responses:
            body = random.choice(questions)
            # return error_response(vars)

        # actual generic response
        if generic_responses:
            body = random.choice(generic_responses)
        # body = random.choice(generic_responses)

        # set confidence
        state_utils.set_confidence(vars, DIALOG_BEGINNING_START_CONFIDENCE)
        # can continue = true - SORT OF
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_SCENARIO)

        # return " ".join([ack, body])
        return body
    except Exception as exc:
        logger.exception(exc)
        logger.info(f"usr_response_to_speech_function_response: Exception: {exc}")
        sentry_sdk.capture_exception(exc)
        return error_response(vars)
