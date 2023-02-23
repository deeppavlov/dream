import json
import logging
import numpy as np
import random
import re
import time
from copy import deepcopy
from os import getenv

import requests
import sentry_sdk
from flask import Flask, request, jsonify
from nltk import pos_tag, tokenize

from common.constants import CAN_NOT_CONTINUE
from common.universal_templates import if_chat_about_particular_topic, if_choose_topic
from common.utils import get_intents, join_sentences_in_or_pattern, join_words_in_or_pattern, get_topics, get_entities
from common.response_selection import ACTIVE_SKILLS

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DEFAULT_ANNTR_HISTORY_LEN = 0
TOP_N_FACTS = 2
AA_FACTOR = 0.05
ABBRS_CONFIDENCE = 0.8
DEFAULT_CONFIDENCE = 0.88
HAS_SPEC_CHAR_CONFIDENCE = 0.0
HIGHEST_CONFIDENCE = 0.99
KG_ACTIVE_DEPTH = 2
LETS_CHAT_ABOUT_CONFIDENDENCE = 0.6
NOUNPHRASE_ENTITY_CONFIDENCE = 0.95
KNOWLEDGE_GROUNDING_SERVICE_URL = getenv("KNOWLEDGE_GROUNDING_SERVICE_URL")
ACTIVE_SKILLS.remove("personal_info_skill")
DFF_SKILLS = deepcopy(ACTIVE_SKILLS)
DFF_ANNTR_HISTORY_LEN = 1

special_char_re = re.compile(r"[^0-9a-zA-Z \-\.\'\?,!]+")
greetings_farewells_re = re.compile(
    join_words_in_or_pattern(
        [
            "have .* day",
            "have .* night",
            ".* bye",
            r"\bbye",
            "goodbye",
            "hello",
            "(it|its|it's|nice|thank you|thanks).* chatting.*",
            "(it|its|it's|nice|thank you|thanks).* talking.*",
            ".* chatting with you.*",
            "hi",
            "good morning",
            "good afternoon",
            "good luck",
            "great chat",
            "get off.*",
            "thanks for the chat",
            "thank.* for .* chat",
        ]
    ),
    re.IGNORECASE,
)
tokenizer = tokenize.RegexpTokenizer(r"\w+")

with open("./google-english-no-swears.txt", "r") as f:
    UNIGRAMS = set(f.read().splitlines())
with open("./abbreviations_acronyms_list.txt", "r") as f:
    ABBRS = re.compile(join_words_in_or_pattern(list(f.read().splitlines())), re.IGNORECASE)
with open("./topics_facts.json") as f:
    TOPICS_FACTS = json.load(f)


def check_dffs(bot_uttrs):
    flag = False
    if len(bot_uttrs) > 1:
        last_utt_skill = bot_uttrs[-1].get("active_skill", "")
        last_but_one_utt_skill = bot_uttrs[-2].get("active_skill", "")
        if last_utt_skill in DFF_SKILLS:
            if last_but_one_utt_skill == last_utt_skill:
                flag = True
    return flag


def get_named_entities(utt):
    entities = []

    for ent in get_entities(utt, only_named=True, with_labels=False):
        if ent not in UNIGRAMS and not (ent == "alexa" and utt["text"].lower()[:5] == "alexa"):
            entities.append(ent)
    return entities


def get_news(uttr, which):
    result_values = []
    annotation = uttr.get("annotations", {}).get("news_api_annotator", [])
    for news_item in annotation:
        if news_item.get("which", "") == which:
            title = news_item.get("news", {}).get("title", "")
            text = news_item.get("news", {}).get("description", "")
            if text:
                result_values.append({"title": title, "description": text})
    return result_values


def get_fact_random(utterances):
    result_values = []
    for i, uttr in enumerate(utterances):
        values = uttr.get("annotations", {}).get("fact_random", {}).get("facts", [])
        if values:
            for v in values:
                value = v.get("fact", "")
                if value:
                    result_values.append([(len(utterances) - i - 1) * 0.01, value])

    return result_values


def get_annotations_from_dialog(utterances, annotator_name, key_name=None):
    """
    Extract list of strings with values of specific key <key_name>
    from annotator <annotator_name> dict from given dialog utterances.

    Args:
        utterances: utterances, the first one is user's reply
        annotator_name: name of target annotator
        key_name: name of target field from annotation dict

    Returns:
        list of strings with values of specific key from specific annotator
    """
    result_values = []
    for i, uttr in enumerate(utterances):
        annotation = uttr.get("annotations", {}).get(annotator_name, {})
        value = ""
        if isinstance(annotation, dict):
            if key_name in annotation:
                # check if odqa has nonempty answer along with a paragraph
                if annotator_name == "kbqa":
                    value = annotation.get(key_name, "")
                # include only non-empty strs
                if value:
                    result_values.append([(len(utterances) - i - 1) * 0.01, value])
            if "facts" in annotation:
                values = deepcopy(annotation["facts"])
                for value in values[:2]:
                    result_values.append([(len(utterances) - i - 1) * 0.01, value])
        if isinstance(annotation, list):
            values = deepcopy(annotation)
            for value in values[:2]:
                result_values.append([(len(utterances) - i - 1) * 0.01, value])

    return result_values


def get_spacy_nounphrases(utt):
    cob_nounphs = get_entities(utt, only_named=False, with_labels=False)
    spacy_nounphrases = []
    for ph in cob_nounphs:
        if not pos_tag([ph])[0][1].startswith("VB"):
            spacy_nounphrases.append(ph)
    return spacy_nounphrases


def get_intents_flags(utt):
    special_intents = [
        "cant_do",
        "repeat",
        "weather_forecast_intent",
        "what_are_you_talking_about",
        "what_can_you_do",
        "what_is_your_job",
        "what_is_your_name",
        "what_time",
        "where_are_you_from",
        "who_made_you",
    ]
    detected_intents = get_intents(utt, which="intent_catcher")
    lets_chat_about_flag = if_chat_about_particular_topic(utt)
    special_intents_flag = any([si in detected_intents for si in special_intents])
    return lets_chat_about_flag, special_intents_flag


def get_lets_chat_topic(lets_chat_about_flag, utt):
    lets_chat_topic = ""
    COBOT_DA_FILE_TOPICS_MATCH = {
        "Entertainment_Movies": "movies",
        "Entertainment_Music": "music",
        "Science_and_Technology": "science",
        "Sports": "sports",
        "Games": "games",
        "Movies_TV": "movies",
        "SciTech": "science",
        "Psychology": "emotions",
        "Music": "music",
        "Food_Drink": "food",
        "Weather_Time": "weather",
        "Entertainment": "activities",
        "Celebrities": "celebrities",
        "Travel_Geo": "travel",
        "Art_Event": "art",
    }
    if lets_chat_about_flag:
        _get_topics = get_topics(utt, which="all")
        for topic in _get_topics:
            if topic in COBOT_DA_FILE_TOPICS_MATCH:
                lets_chat_topic = COBOT_DA_FILE_TOPICS_MATCH[topic]
                if lets_chat_topic not in utt["text"]:
                    lets_chat_topic = ""
    return lets_chat_topic


def get_news_api_fact(bot_uttr, human_uttrs, not_switch_or_lets_chat_flag):
    news_api_fact = ""
    if len(human_uttrs) > 1:
        if (bot_uttr.get("active_skill", "") == "news_api_skill") and not_switch_or_lets_chat_flag:
            prev_human_utt_hypotheses = human_uttrs[-2].get("hypotheses", [])
            news_api_hypothesis = [
                h for h in prev_human_utt_hypotheses if (h.get("skill_name", "") == "news_api_skill")
            ]
            if news_api_hypothesis:
                if news_api_hypothesis[0].get("news_status", "") == "opinion_request":
                    news_api_fact = news_api_hypothesis[0].get("curr_news", {}).get("description", "")
    return news_api_fact


def get_knowledge_from_annotators(annotators, uttrs, anntr_history_len):
    user_input_knowledge = ""
    anntrs_knowledge = ""
    # look for kbqa/odqa text in anntr_history_len previous human utterances
    annotations_depth = {}
    for anntr_name, anntr_key in annotators.items():
        prev_anntr_outputs = get_annotations_from_dialog(uttrs[-anntr_history_len * 2 - 1 :], anntr_name, anntr_key)
        logger.debug(f"Prev {anntr_name} {anntr_key}s: {prev_anntr_outputs}")
        # add final dot to kbqa answer to make it a sentence
        if prev_anntr_outputs and anntr_name == "kbqa":
            prev_anntr_outputs[-1][1] += "."
        # concat annotations separated by space to make a paragraph
        if prev_anntr_outputs and prev_anntr_outputs[-1][1] != "Not Found":
            anntrs_knowledge += prev_anntr_outputs[-1][1] + " "
            annotations_depth[anntr_name] = prev_anntr_outputs[-1][0]
    if anntrs_knowledge:
        user_input_knowledge += "\n".join(tokenize.sent_tokenize(anntrs_knowledge))
    return user_input_knowledge, annotations_depth


def space_join(x):
    return " ".join(x) + " " if x else ""


def get_penalties(bot_uttrs, curr_response):
    already_was_active = 0
    if bot_uttrs:
        for bu in range(1, 1 + min(KG_ACTIVE_DEPTH, len(bot_uttrs))):
            already_was_active += int(bot_uttrs[-bu].get("active_skill", "") == "knowledge_grounding_skill")
    already_was_active *= AA_FACTOR
    resp_tokens_len = len(tokenizer.tokenize(curr_response))
    short_long_response = 0.5 * int(resp_tokens_len > 20 or resp_tokens_len < 4)
    return already_was_active, short_long_response


@app.route("/respond", methods=["POST"])
def respond():
    print("response generation started")
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    # following 3 lists have len = number of samples going to the model
    annotations_depths = []
    dial_ids = []
    input_batch = []
    # following 4 lists have len = len(dialogs_batch)
    entities = []
    lets_chat_about_flags = []
    nounphrases = []
    special_intents_flags = []
    chosen_topics = {}
    for d_id, dialog in enumerate(dialogs_batch):
        try:
            user_input_text = dialog["human_utterances"][-1]["text"]
            bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {}
            switch_choose_topic = if_choose_topic(dialog["human_utterances"][-1], bot_uttr)
            # spacy_nounphrases
            spacy_nounphrases = get_spacy_nounphrases(dialog["human_utterances"][-1])
            nounphrases.append(
                re.compile(join_sentences_in_or_pattern(spacy_nounphrases), re.IGNORECASE) if spacy_nounphrases else ""
            )
            # entities
            curr_ents = get_named_entities(dialog["human_utterances"][-1])
            entities.append(re.compile(join_sentences_in_or_pattern(curr_ents), re.IGNORECASE) if curr_ents else "")
            # intents
            lets_chat_about_flag, special_intents_flag = get_intents_flags(dialog["human_utterances"][-1])
            lets_chat_about_flags.append(lets_chat_about_flag)
            special_intents_flags.append(special_intents_flag)

            anntr_history_len = DEFAULT_ANNTR_HISTORY_LEN
            bot_uttrs_for_dff_check = dialog["bot_utterances"][-2:] if len(dialog["bot_utterances"]) > 1 else []
            dffs_flag = check_dffs(bot_uttrs_for_dff_check)
            if lets_chat_about_flag or switch_choose_topic:
                anntr_history_len = 0
            elif dffs_flag:
                anntr_history_len = DFF_ANNTR_HISTORY_LEN
            # if detected lets_chat is about topic from the file
            lets_chat_topic = get_lets_chat_topic(lets_chat_about_flag, dialog["human_utterances"][-1])
            # if prev skill == news_api_skill get news description and create knowledge fact
            news_api_fact = get_news_api_fact(
                bot_uttr, dialog["human_utterances"], not (switch_choose_topic or lets_chat_about_flag)
            )
            # start creating data for kg service
            user_input_history = "\n".join([i["text"] for i in dialog["utterances"]])

            annotators = {
                # "odqa": "answer_sentence",
                # "kbqa": "answer"
            }
            if not switch_choose_topic:
                user_input_knowledge, annotations_depth = get_knowledge_from_annotators(
                    annotators, dialog["utterances"], anntr_history_len
                )
            else:
                user_input_knowledge = ""
                annotations_depth = {}
            # add nounphrases and entities to the knowledge
            if user_input_knowledge:
                user_input_checked_sentence = (
                    space_join(spacy_nounphrases)
                    + space_join(curr_ents)
                    + tokenize.sent_tokenize(user_input_knowledge)[0]
                )
            else:
                user_input_checked_sentence = ""

            if user_input_knowledge:
                user_input = {
                    "checked_sentence": user_input_checked_sentence,
                    "knowledge": user_input_knowledge,
                    "text": user_input_text,
                    "history": user_input_history,
                }
                annotations_depths.append(annotations_depth)
                dial_ids.append(d_id)
                input_batch.append(user_input)

            retrieved_facts = get_annotations_from_dialog(
                dialog["utterances"][-anntr_history_len * 2 - 1 :], "fact_retrieval"
            )
            if retrieved_facts:
                for depth, fact in retrieved_facts[-TOP_N_FACTS:]:
                    user_input = {
                        "checked_sentence": fact,
                        "knowledge": fact,
                        "text": user_input_text,
                        "history": user_input_history,
                    }
                    input_batch.append(user_input)
                    annotations_depths.append({"retrieved_fact": depth})
                    dial_ids.append(d_id)

            if any([switch_choose_topic, lets_chat_topic, lets_chat_about_flag]):
                if lets_chat_topic:
                    fact = random.sample(TOPICS_FACTS[lets_chat_topic], 1)[0]
                    chosen_topics[d_id] = lets_chat_topic
                    _chosen_topic_fact = "lets_chat_cobot_da"
                elif not get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False):
                    topic = random.sample(TOPICS_FACTS.keys(), 1)[0]
                    fact = random.sample(TOPICS_FACTS[topic], 1)[0]
                    chosen_topics[d_id] = topic
                    _chosen_topic_fact = "switch_random"
                else:
                    fact = ""
                if fact:
                    user_input = {
                        "checked_sentence": fact,
                        "knowledge": fact,
                        "text": user_input_text,
                        "history": user_input_history,
                        "chosen_topic_fact": _chosen_topic_fact,
                    }
                    input_batch.append(user_input)
                    annotations_depths.append({})
                    dial_ids.append(d_id)

            if news_api_fact:
                user_input = {
                    "checked_sentence": news_api_fact,
                    "knowledge": news_api_fact,
                    "text": user_input_text,
                    "history": user_input_history,
                    "news_api_fact": True,
                }
                input_batch.append(user_input)
                annotations_depths.append({})
                dial_ids.append(d_id)

            fact_random_facts = get_fact_random(dialog["utterances"][-anntr_history_len * 2 - 1 :])
            if fact_random_facts:
                user_input = {
                    "checked_sentence": fact_random_facts[-1][1],
                    "knowledge": fact_random_facts[-1][1],
                    "text": user_input_text,
                    "history": user_input_history,
                    "fact_random_fact": True,
                }
                input_batch.append(user_input)
                annotations_depths.append({"fact_random": fact_random_facts[-1][0]})
                dial_ids.append(d_id)

            user_news = get_news(dialog["human_utterances"][-1], "human")
            bot_news = get_news(dialog["human_utterances"][-1], "bot")
            # all_news = get_news(dialog["human_utterances"][-1], "all")
            if user_news:
                news_desc = user_news[-1].get("decsription", "")
                if news_desc:
                    user_input = {
                        "checked_sentence": news_desc,
                        "knowledge": news_desc,
                        "text": user_input_text,
                        "history": user_input_history,
                        "news_fact": "human ",
                    }
                    input_batch.append(user_input)
                    annotations_depths.append({})
                    dial_ids.append(d_id)
            elif bot_news:
                news_desc = bot_news[-1].get("decsription", "")
                if news_desc:
                    user_input = {
                        "checked_sentence": news_desc,
                        "knowledge": news_desc,
                        "text": user_input_text,
                        "history": user_input_history,
                        "news_fact": "bot ",
                    }
                    input_batch.append(user_input)
                    annotations_depths.append({})
                    dial_ids.append(d_id)
            # elif all_news:
            #     user_input = {
            #         'checked_sentence': all_news[-1].get("decsription", ""),
            #         'knowledge': all_news[-1].get("decsription", ""),
            #         'text': user_input_text,
            #         'history': user_input_history,
            #         'news_fact': "all ",
            #         'news_title': all_news[-1].get("title", "")
            #     }
            #     input_batch.append(user_input)
            #     annotations_depths.append({})
            #     dial_ids.append(d_id)

        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            logger.exception(ex)

    try:
        raw_responses = []
        if input_batch:
            logger.info(f"skill sends to service: {input_batch}")
            resp = requests.post(KNOWLEDGE_GROUNDING_SERVICE_URL, json={"batch": input_batch}, timeout=1.5)
            raw_responses = resp.json()
            logger.info(f"skill receives from service: {raw_responses}")
        else:
            responses = [[""]]
            confidences = [[0.0]]
            attributes = [[{}]]
            logger.info(f"Collected no hypotheses, exiting with {list(zip(responses, confidences, attributes))}")
            return jsonify(list(zip(responses, confidences, attributes)))

        dial_ids = np.array(dial_ids)
        attributes = []
        confidences = []
        responses = []

        for i, dialog in enumerate(dialogs_batch):
            curr_attributes = []
            curr_confidences = []
            curr_responses = []
            for curr_i in np.where(dial_ids == i)[0]:
                attr = {
                    "knowledge_paragraph": input_batch[curr_i]["knowledge"],
                    "knowledge_checked_sentence": input_batch[curr_i]["checked_sentence"],
                    "can_continue": CAN_NOT_CONTINUE,
                    "confidence_case": "",
                }

                already_was_active, short_long_response = get_penalties(dialog["bot_utterances"], raw_responses[curr_i])
                curr_nounphrase_search = nounphrases[i].search(raw_responses[curr_i]) if nounphrases[i] else False
                curr_entities_search = entities[i].search(raw_responses[curr_i]) if entities[i] else False
                no_penalties = False
                fact_random_penalty = 0.0

                topic = chosen_topics.get(i, "")
                chosen_topic_fact_flag = input_batch[curr_i].get("chosen_topic_fact", "")
                curr_news_fact = input_batch[curr_i].get("news_fact", "")

                add_intro = ""
                if topic and chosen_topic_fact_flag:
                    add_intro = f"Okay, Let's chat about {topic}. "
                    confidence = HIGHEST_CONFIDENCE
                    no_penalties = True
                    attr["confidence_case"] += f"topic_fact: {chosen_topic_fact_flag} "
                    attr["response_parts"] = ["prompt"]
                elif input_batch[curr_i].get("news_api_fact", ""):
                    add_intro = random.choice(
                        [
                            "Sounds like ",
                            "Seems like ",
                            "Makes sense. ",
                            # "Here's what I've heard: ", "Here's something else I've heard: ",
                            "It reminds me that ",
                            "This comes to my mind: ",
                            "",
                        ]
                    )
                    no_penalties = True
                    confidence = HIGHEST_CONFIDENCE
                    attr["confidence_case"] += "news_api_fact "
                elif input_batch[curr_i].get("fact_random_fact", ""):
                    fact_random_penalty = annotations_depths[curr_i].get("fact_random", 0.0)
                    confidence = DEFAULT_CONFIDENCE
                    attr["confidence_case"] += "fact_random_fact "
                elif curr_news_fact:
                    if curr_news_fact != "all":
                        confidence = NOUNPHRASE_ENTITY_CONFIDENCE
                    else:
                        confidence = DEFAULT_CONFIDENCE
                        curr_news_title = input_batch[curr_i].get("news_title", "")
                        if curr_news_title:
                            add_intro = f"I have just read that {curr_news_title}. "
                    attr["confidence_case"] += "news_fact: " + curr_news_fact
                elif (curr_nounphrase_search or curr_entities_search) and lets_chat_about_flags[i]:
                    confidence = HIGHEST_CONFIDENCE
                    attr["confidence_case"] += "nounphrase_entity_and_lets_chat_about "
                    attr["response_parts"] = ["prompt"]
                elif curr_nounphrase_search or curr_entities_search:
                    confidence = NOUNPHRASE_ENTITY_CONFIDENCE
                    attr["confidence_case"] += "nounphrase_entity "
                elif lets_chat_about_flags[i]:
                    confidence = LETS_CHAT_ABOUT_CONFIDENDENCE
                    attr["confidence_case"] += "lets_chat_about "
                    attr["response_parts"] = ["prompt"]
                else:
                    confidence = DEFAULT_CONFIDENCE
                    attr["confidence_case"] += "default "

                acronym_flag = ABBRS.search(raw_responses[curr_i])
                if acronym_flag:
                    confidence = ABBRS_CONFIDENCE
                    attr["confidence_case"] += f"acronyms: {acronym_flag} "
                    logger.debug(f"KG skill: found acronyms: {acronym_flag}")
                special_char_flag = special_char_re.search(raw_responses[curr_i])
                if special_char_flag:
                    confidence = HAS_SPEC_CHAR_CONFIDENCE
                    attr["confidence_case"] += "special_char "
                    logger.debug(f"KG skill: found special_char: {special_char_flag}")
                if special_intents_flags[i]:
                    confidence = 0.0
                    attr["confidence_case"] += "special_intents "
                    logger.debug("KG skill: found special_intents")
                greetings_farewells_flag = greetings_farewells_re.search(raw_responses[curr_i])
                if greetings_farewells_flag:
                    confidence = 0.0
                    attr["confidence_case"] += "greetings_farewells "
                    logger.debug(f"KG skill: found greetings_farewells: {greetings_farewells_flag}")

                penalties = (
                    annotations_depths[curr_i].get("retrieved_fact", 0.0)
                    + fact_random_penalty
                    + already_was_active
                    + short_long_response
                    if not no_penalties
                    else 0.0
                )
                confidence -= penalties
                if any(
                    [
                        acronym_flag,
                        special_char_flag,
                        special_intents_flags[i],
                        greetings_farewells_flag,
                        short_long_response,
                    ]
                ):
                    logger.debug(f"KG skill: found penalties in response: {raw_responses[curr_i]}, skipping it")
                    continue
                else:
                    curr_attributes.append(attr)
                    curr_confidences.append(max(0.0, confidence))
                    curr_responses.append(
                        re.sub(r'\s([?.!",;:](?:\s|$))', r"\1", add_intro + raw_responses[curr_i]).replace(" ' t", "'t")
                    )
            attributes.append(curr_attributes)
            confidences.append(curr_confidences)
            responses.append(curr_responses)

    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        logger.exception(ex)
        responses = [[""]]
        confidences = [[0.0]]
        attributes = [[{}]]

    logger.info(f"knowledge_grounding_skill exec time: {time.time() - st_time}")
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
