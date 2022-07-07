#!/usr/bin/env python

import logging
import time
import re

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE, MUST_CONTINUE
from common.personal_info import (
    NON_GEOGRAPHICAL_LOCATIONS_COMPILED_PATTERN,
    REPEAT_INFO_PHRASES,
    ASK_GEOGRAPHICAL_LOCATION_BECAUSE_USER_MISUNDERSTOOD_BOT,
    MAX_READABLE_NAME_WORD_LEN,
    TELL_USER_HIS_INFO_RESPONSE,
    RESPONSE_PHRASES,
    TELL_MY_COMPILED_PATTERNS,
    BOT_KNOWS_INFO_KEY,
    BOT_DOESNT_KNOW_INFO_KEY,
    BOT_DOESNT_KNOW_USER_INFO_RESPONSES,
    ASK_USER_ABOUT_NAME_AGAIN_RESPONSE,
    AS_YOU_WISH_RESPONSE,
    WHERE_DO_YOU_LIVE_NOW_RESPONSE,
    NEVER_HEARD_OF_NAME_RESPONSE,
    WHICH_INFO_RU_MAP,
    where_are_you_from_pattern,
    what_is_your_location_pattern,
    is_secret_patterns,
    my_name_is_not_pattern,
    what_is_your_name_pattern,
    my_location_is_pattern,
    my_name_is_pattern,
    my_origin_is_pattern,
    how_do_you_know_my_info_patterns,
    how_do_you_know_my_info_responses,
)
from common.utils import get_entities, get_named_locations, get_named_persons, is_no, is_yes


sentry_sdk.init(getenv("SENTRY_DSN"))
LANGUAGE = getenv("LANGUAGE", "EN")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
RESPONSE_PHRASES = RESPONSE_PHRASES[LANGUAGE]
BOT_DOESNT_KNOW_USER_INFO_RESPONSES = BOT_DOESNT_KNOW_USER_INFO_RESPONSES[LANGUAGE]


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []
    attributes = []

    for dialog in dialogs_batch:
        human_attr, bot_attr = {}, {}
        response, confidence, attr = how_do_you_know_my_info(dialog, which_info="name")
        logger.info(f"how_do_you_know_my_info `name` returns {response}")
        if confidence == 0.0:
            response, confidence, attr = how_do_you_know_my_info(dialog, which_info="location")
            logger.info(f"how_do_you_know_my_info `location` returns {response}")
        if confidence == 0.0:
            response, confidence, attr = how_do_you_know_my_info(dialog, which_info="homeland")
            logger.info(f"how_do_you_know_my_info `homeland` returns {response}")

        if confidence == 0.0:
            response, confidence, human_attr, bot_attr, attr = process_info(dialog, which_info="name")
            logger.info(f"process_info `name` returns {response}")

        if confidence == 0.0:
            response, confidence, human_attr, bot_attr, attr = process_info(dialog, which_info="homeland")
            logger.info(f"process_info `homeland` returns {response}")

        if confidence == 0.0:
            response, confidence, human_attr, bot_attr, attr = process_info(dialog, which_info="location")
            logger.info(f"process_info `location` returns {response}")

        if confidence == 0.0:
            response, confidence, attr = tell_my_info(dialog, which_info="name")
            logger.info(f"tell_my_info `name` returns {response}")

        if confidence == 0.0:
            response, confidence, attr = tell_my_info(dialog, which_info="location")
            logger.info(f"tell_my_info `location` returns {response}")

        if confidence == 0.0:
            response, confidence, attr = tell_my_info(dialog, which_info="homeland")
            logger.info(f"tell_my_info `homeland` returns {response}")

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)
        attributes.append(attr)

    total_time = time.time() - st_time
    logger.info(f"personal_info_skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


def did_user_misunderstand_bot_question_about_geography(found_info_or_user_text, which_info, prev_bot_text):
    logger.info(f"found_info_or_user_text: {found_info_or_user_text}")
    logger.info(f"which_info: {which_info}")
    logger.info(f"prev_bot_text: {prev_bot_text}")
    return (
        which_info != "name"
        and NON_GEOGRAPHICAL_LOCATIONS_COMPILED_PATTERN.search(found_info_or_user_text)
        and (
            where_are_you_from_pattern.search(prev_bot_text)
            or what_is_your_location_pattern.search(prev_bot_text)
            or REPEAT_INFO_PHRASES[which_info][LANGUAGE].lower() in prev_bot_text
        )
    )


def was_user_asked_to_clarify_info(prev_bot_text, which_info):
    if which_info == "name":
        res = prev_bot_text == REPEAT_INFO_PHRASES[which_info][LANGUAGE].lower()
    else:
        res = (
            prev_bot_text == REPEAT_INFO_PHRASES[which_info][LANGUAGE].lower()
            or prev_bot_text == ASK_GEOGRAPHICAL_LOCATION_BECAUSE_USER_MISUNDERSTOOD_BOT[which_info][LANGUAGE].lower()
        )
    return res


def filter_unreadable_names(found_name):
    words = found_name.split()
    max_word_len = max([len(w) for w in words])
    if max_word_len > MAX_READABLE_NAME_WORD_LEN or len(words) > 4:
        filtered_result = None
    else:
        filtered_result = found_name
    return filtered_result


def shorten_long_names(found_name):
    words = found_name.split()
    if len(words) > 2:
        shortened_result = words[0]
    else:
        shortened_result = found_name
    return shortened_result


def is_secret(user_text, which_info):
    return bool(is_secret_patterns[which_info].search(user_text.lower()))


def user_tells_bot_called_him_wrong(curr_human_annotated_uttr, prev_bot_text, user_profile):
    name = user_profile.get("name")

    lang_which_info = "имя" if LANGUAGE == "RU" else "name"
    res = my_name_is_not_pattern.search(curr_human_annotated_uttr.get("text", "")) or (
        TELL_USER_HIS_INFO_RESPONSE[LANGUAGE].format(which_info=lang_which_info, info=name).lower() in prev_bot_text
        and is_no(curr_human_annotated_uttr)
    )
    return res


def process_info(dialog, which_info="name"):
    human_attr = {}
    bot_attr = {}
    attr = {"can_continue": CAN_NOT_CONTINUE}
    response = ""
    confidence = 0.0

    curr_uttr_dict = dialog["human_utterances"][-1]
    curr_user_uttr = curr_uttr_dict["text"].lower()
    curr_user_annot = curr_uttr_dict["annotations"]
    bot_utterance_texts = [u["text"].lower() for u in dialog["bot_utterances"]]
    prev_bot_uttr = bot_utterance_texts[-1] if len(bot_utterance_texts) > 0 else ""

    is_about_templates = {
        "name": what_is_your_name_pattern.search(prev_bot_uttr) or my_name_is_pattern.search(curr_user_uttr),
        "homeland": where_are_you_from_pattern.search(prev_bot_uttr) or my_origin_is_pattern.search(curr_user_uttr),
        "location": what_is_your_location_pattern.search(prev_bot_uttr)
        or my_location_is_pattern.search(curr_user_uttr),
    }
    response_phrases = {
        "name": RESPONSE_PHRASES["name"][0],
        "location": RESPONSE_PHRASES["location"][1]
        if RESPONSE_PHRASES["location"][0].lower() in bot_utterance_texts
        else RESPONSE_PHRASES["location"][0],
        "homeland": RESPONSE_PHRASES["homeland"][1]
        if RESPONSE_PHRASES["homeland"][0].lower() in bot_utterance_texts
        else RESPONSE_PHRASES["homeland"][0],
    }

    got_info = False
    # if user doesn't want to share his info
    if user_tells_bot_called_him_wrong(curr_uttr_dict, prev_bot_uttr, dialog["human"]["profile"]):
        logger.info("User says My name is not Blabla. Clarify name again")
        response = ASK_USER_ABOUT_NAME_AGAIN_RESPONSE[LANGUAGE]
        confidence = 1.0
        got_info = True
        attr["can_continue"] = MUST_CONTINUE
    elif (is_about_templates[which_info] or was_user_asked_to_clarify_info(prev_bot_uttr, which_info)) and (
        is_no(curr_uttr_dict) or is_secret(curr_user_uttr, which_info)
    ):
        logger.info("User does not want to share private info. Finish")
        response = AS_YOU_WISH_RESPONSE[LANGUAGE]
        confidence = 1.0
        attr["can_continue"] = CAN_NOT_CONTINUE
        return response, confidence, human_attr, bot_attr, attr
    elif re.search(RESPONSE_PHRASES["homeland"][0], prev_bot_uttr, re.IGNORECASE) and is_yes(curr_uttr_dict):
        logger.info("Found location=homeland")
        if dialog["human"]["attributes"].get("homeland", None):
            human_attr["location"] = dialog["human"]["attributes"]["homeland"]
        else:
            found_homeland = check_entities(
                "homeland",
                curr_user_uttr=dialog["human_utterances"][-2]["text"].lower(),
                curr_user_annot=dialog["human_utterances"][-2]["annotations"],
                prev_bot_uttr=dialog["bot_utterances"][-2]["text"].lower(),
            )
            human_attr["location"] = found_homeland
        response = response_phrases["location"]
        confidence = 1.0
        got_info = True
        attr["can_continue"] = MUST_CONTINUE
    elif re.search(RESPONSE_PHRASES["homeland"][0], prev_bot_uttr, re.IGNORECASE) and is_no(curr_uttr_dict):
        logger.info("Found location is not homeland")
        response = WHERE_DO_YOU_LIVE_NOW_RESPONSE[LANGUAGE]
        confidence = 1.0
        got_info = False
        attr["can_continue"] = MUST_CONTINUE

    if (is_about_templates[which_info] or was_user_asked_to_clarify_info(prev_bot_uttr, which_info)) and not got_info:
        logger.info(f"Asked for {which_info} in {prev_bot_uttr}")
        found_info, named_entities_found = check_entities(which_info, curr_user_uttr, curr_user_annot, prev_bot_uttr)
        logger.info(f"found_info, named_entities_found: {found_info}, {named_entities_found}")
        if which_info == "name" and found_info is not None:
            found_info = filter_unreadable_names(found_info)
        if found_info is None:
            logger.info("found_info is None")
            if did_user_misunderstand_bot_question_about_geography(curr_user_uttr, which_info, prev_bot_uttr):
                response = ASK_GEOGRAPHICAL_LOCATION_BECAUSE_USER_MISUNDERSTOOD_BOT[which_info][LANGUAGE]
                confidence = 0.9
                attr["can_continue"] = CAN_CONTINUE_SCENARIO
            elif which_info in ["homeland", "location"] and NON_GEOGRAPHICAL_LOCATIONS_COMPILED_PATTERN.search(
                curr_user_uttr
            ):
                response = ""
                confidence = 0.0
                attr["can_continue"] = CAN_NOT_CONTINUE
            elif was_user_asked_to_clarify_info(prev_bot_uttr, which_info):
                response = ""
                confidence = 0.0
                attr["can_continue"] = CAN_NOT_CONTINUE
            elif (
                which_info == "name"
                and len(curr_user_uttr.split()) == 1
                and len(get_entities(curr_uttr_dict, only_named=False, with_labels=False)) > 0
            ):
                response = NEVER_HEARD_OF_NAME_RESPONSE[LANGUAGE]
                confidence = 1.0
                attr["can_continue"] = MUST_CONTINUE
            else:
                response = REPEAT_INFO_PHRASES[which_info][LANGUAGE]
                confidence = 1.0
                attr["can_continue"] = MUST_CONTINUE
        else:
            if which_info == "name":
                found_info = shorten_long_names(found_info)
                response = response_phrases[which_info] + found_info + "."
                confidence = 1.0
                attr["can_continue"] = MUST_CONTINUE
                human_attr[which_info] = found_info
            else:
                if NON_GEOGRAPHICAL_LOCATIONS_COMPILED_PATTERN.search(found_info):
                    if did_user_misunderstand_bot_question_about_geography(found_info, which_info, prev_bot_uttr):
                        response = ASK_GEOGRAPHICAL_LOCATION_BECAUSE_USER_MISUNDERSTOOD_BOT[which_info][LANGUAGE]
                        confidence = 0.9
                        attr["can_continue"] = CAN_CONTINUE_SCENARIO
                    else:
                        response = ""
                        confidence = 0.0
                        attr["can_continue"] = CAN_NOT_CONTINUE
                else:
                    if which_info == "location":
                        response = response_phrases[which_info]
                    elif which_info == "homeland":
                        if dialog["human"]["profile"].get("location", None) is None:
                            response = response_phrases[which_info]
                        else:
                            response = response_phrases["location"]
                    human_attr[which_info] = found_info
                    if named_entities_found:
                        confidence = 1.0
                        attr["can_continue"] = MUST_CONTINUE
                    else:
                        confidence = 0.9
                        attr["can_continue"] = CAN_CONTINUE_SCENARIO
    return response, confidence, human_attr, bot_attr, attr


def how_do_you_know_my_info(dialog, which_info="name"):
    curr_user_uttr = dialog["human_utterances"][-1]["text"].lower()
    how_do_you_know_search_result = how_do_you_know_my_info_patterns[which_info].search(curr_user_uttr)
    if how_do_you_know_search_result is None:
        response = ""
        confidence = 0.0
        attr = {}
    else:
        if dialog.get("human", {}).get("profile", {}).get(which_info, ""):
            response = how_do_you_know_my_info_responses[which_info][BOT_KNOWS_INFO_KEY][LANGUAGE]
        else:
            response = how_do_you_know_my_info_responses[which_info][BOT_DOESNT_KNOW_INFO_KEY][LANGUAGE]
        confidence = 1.0
        attr = {"can_continue": MUST_CONTINUE}
    return response, confidence, attr


def tell_my_info(dialog, which_info="name"):
    response = ""
    confidence = 0.0
    attr = {}

    curr_user_uttr = dialog["human_utterances"][-1]["text"].lower()
    if TELL_MY_COMPILED_PATTERNS[which_info].search(curr_user_uttr):
        logger.info(f"Asked to memorize user's {which_info} in {curr_user_uttr}")
        if dialog["human"]["profile"].get(which_info, None) is None:
            response = BOT_DOESNT_KNOW_USER_INFO_RESPONSES[which_info]
            confidence = 1.0
            attr["can_continue"] = MUST_CONTINUE
        else:
            name = dialog["human"]["profile"][which_info]
            lang_which_info = WHICH_INFO_RU_MAP[which_info] if LANGUAGE == "RU" else which_info
            response = TELL_USER_HIS_INFO_RESPONSE[LANGUAGE].format(which_info=lang_which_info, info=name)
            confidence = 1.0
            attr["can_continue"] = MUST_CONTINUE
    return response, confidence, attr


def extract_possible_names(annotated_utterance, only_named, with_labels):
    entities = get_entities(
        annotated_utterance,
        only_named=only_named,
        with_labels=with_labels,
    )
    if not only_named:
        nounphrases = annotated_utterance["annotations"].get("spacy_nounphrases", [])
        if with_labels:
            nounphrases = [{"text": np, "label": "misc"} for np in nounphrases]
        entities += nounphrases
    return entities


def check_entities(which_info, curr_user_uttr, curr_user_annot, prev_bot_uttr):
    found_info = None

    if which_info == "name":
        named_entities = get_named_persons({"text": curr_user_uttr, "annotations": curr_user_annot})
    else:
        named_entities = get_named_locations({"text": curr_user_uttr, "annotations": curr_user_annot})
    logger.info(f"(check_entities)named_entities: {named_entities}")
    if len(named_entities) == 0:
        # try to search in all types of NAMED entities
        named_entities = []
        for ent in extract_possible_names(
            {"text": curr_user_uttr, "annotations": curr_user_annot},
            only_named=False,
            with_labels=True,
        ):
            logger.info(f"(check_entities)ent: {ent}")
            if "my name is" == ent["text"].lower() or "call me" == ent["text"].lower():
                continue
            if ent["text"].lower() == "alexa":
                # this is working only for English
                if re.search(r"(my (name is|name's)|call me) alexa", curr_user_uttr, re.IGNORECASE) or (
                    re.search(r"(what is|what's|whats|tell me) your? name", prev_bot_uttr, re.IGNORECASE)
                    and re.match(r"^alexa[.,!?]*$", curr_user_uttr)
                ):
                    # - my name is alexa
                    # - what's your name? - alexa.
                    pass
                else:
                    # in all other cases skip alexa
                    continue
            if re.search(
                r"^" + ent["text"] + r"[.,!?]*$|" + my_name_is_pattern.pattern + " +" + ent["text"],
                curr_user_uttr,
                re.IGNORECASE,
            ):
                named_entities.append(ent["text"])
            elif (which_info == "name" and ent.get("type", "") == "PER") or (
                which_info in ["homeland", "location"] and ent.get("type", "") == "LOC"
            ):
                named_entities.append(ent["text"])

    if named_entities:
        ent = named_entities[-1]
        found_info = " ".join([n.capitalize() for n in ent.split()])
    logger.info(f"Found {which_info} `{found_info}`")
    return found_info, bool(named_entities)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
