# %%
import os
import logging
import re

import requests

import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
import common.custom_requests as custom_requests

import common.utils as common_utils

import dialogflows.scenarios.gossip as this_gossip

import common.gossip as common_gossip

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

ENTITY_LINKING_URL = os.getenv("ENTITY_LINKING_URL")
WIKIDATA_URL = os.getenv("WIKIDATA_URL")
assert ENTITY_LINKING_URL, ENTITY_LINKING_URL
assert WIKIDATA_URL, WIKIDATA_URL

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

##################################################################################################################
# Entity Linking & Wiki Parser
##################################################################################################################


def request_el_wp_entities(person, utterance):
    entities_info = {}
    try:
        el_output = requests.post(
            ENTITY_LINKING_URL,
            json={"entity_substr": [[person]], "template": [""], "context": [[utterance]]},
            timeout=0.8,
        ).json()
        entity_info = el_output and el_output[0] and el_output[0][0]
        if isinstance(entity_info, list) and entity_info and entity_info[0]:
            entity_ids = entity_info[0]
            entity_id = entity_ids[0]
            wp_output = requests.post(
                WIKIDATA_URL,
                json={"parser_info": ["find_top_triplets"], "query": [[[entity_id]]]},
                timeout=0.8,
            ).json()
        elif isinstance(entity_info, dict):
            entity_ids = entity_info.get("entity_ids", [])
            entity_id = entity_ids and entity_ids[0]
            wp_output = (entity_id and requests.post(WIKIDATA_URL, json={
                "parser_info": ["find_top_triplets"],
                "query": [[{"entity_substr": person, "entity_ids": [entity_id]}]]}, timeout=0.8).json())
        else:
            raise Exception(entities_info)
        entities_info = wp_output and wp_output[0].get("entities_info", {})
    except Exception as exc:
        msg = f"request_el_wp_entities exception: {exc}"
        logger.debug(msg)
        sentry_sdk.capture_message(msg)
    return entities_info if entities_info else {}


def get_relationship_between_two_people(person_1, person_2):
    wp_output = []
    try:
        persons = [person_1, person_2]
        el_output = requests.post(
            ENTITY_LINKING_URL,
            json={"entity_substr": [persons], "template": [""], "context": [[""]]},
            timeout=0.8,
        ).json()
        entity_info_list = el_output and el_output[0]
        if entity_info_list:
            if (
                isinstance(entity_info_list[0], list)
                and len(entity_info_list[0]) == 2
                and entity_info_list[0][0]
                and entity_info_list[0][1]
            ):
                entities1, entities2 = entity_info_list[0]
            if isinstance(entity_info_list[0], dict) and len(entity_info_list) == 2:
                entities1, entities2 = entity_info_list
                entities1 = entities1.get("entity_ids", [])
                entities2 = entities2.get("entity_ids", [])

        wp_output = requests.post(
            WIKIDATA_URL,
            json={"parser_info": ["find_connection"], "query": [[entities1, entities2]]},
            timeout=0.8,
        ).json()
    except Exception as exc:
        msg = f"request_relationship_between_two_people exception: {exc}"
        logger.debug(msg)
        sentry_sdk.capture_message(msg)

    relationship = wp_output and wp_output[0] and wp_output[0][0]

    return relationship


def get_occupations_for_person_from_wiki_parser(person, utterance):
    occupations = []

    entities_info = request_el_wp_entities(person, utterance)

    logger.debug(f"Get Occupations: {entities_info}")

    for entity_label in entities_info:
        triplets = entities_info[entity_label]
        logger.debug(triplets)
        if "occupation" in triplets:
            occupations += [triplets["occupation"]]

    return occupations


def get_gender_age_person(person, utterance):
    gender = "unknown"
    age = 0

    entities_info = request_el_wp_entities(person, utterance)

    for entity_label in entities_info:
        triplets = entities_info[entity_label]
        gender = triplets.get("gender", [])
        age = triplets.get("age", 0)

        gender = gender and gender[0] and gender[0][1]
        gender = gender if gender else "they"
    return gender, age


# def is_creative_person(person, utterance):
#     entities_info = request_el_wp_entities(person, utterance)

#     for entity_label in entities_info:
#         triplets = entities_info[entity_label]

#         occupations = triplets["occupation"]
#         occupation_titles = set([occ_title for occ_id, occ_title in occupations])

#     sports_occupations = this_news.COBOT_TOPICS_TO_WIKI_OCCUPATIONS["Sports"]

#     is_sports_person = False

#     for occupation_title in occupation_titles:
#         if occupation_title in sports_occupations:
#             is_sports_person = True

#     return is_sports_person


def get_teams_for_sportsperson(person, utterance):
    sport = [[]]
    teams = [[]]

    entities_info = request_el_wp_entities(person, utterance)

    for entity_label in entities_info:
        triplets = entities_info[entity_label]

    sport = triplets.get("sport", [[]])
    teams = triplets.get("member of sports team", [[]])

    return sport, teams


def get_spouse_or_partner_person(person, utterance):
    spouse = ""
    partner = ""

    entities_info = request_el_wp_entities(person, utterance)

    for entity_label in entities_info:
        triplets = entities_info[entity_label]
        spouse = triplets.get("spouse", [])
        partner = triplets.get("partner", [])
        spouse = spouse[0][1] if spouse else None
        partner = partner[0][1] if partner else None

    return spouse, partner


def get_human_readable_gender_statement_current_is(gender: str):
    if "female" in gender.lower():
        return "she is"
    if "male" in gender.lower():
        return "he is"
    return "they are"


def get_human_readable_gender_statement_current_eir(gender: str):
    if "female" in gender.lower():
        return "her"
    if "male" in gender.lower():
        return "his"
    return "their"


def get_human_readable_gender_statement_current_im(gender: str):
    if "female" in gender.lower():
        return "her"
    if "male" in gender.lower():
        return "him"
    return "them"


def get_notable_works_for_creative_person(person, utterance):
    films = []
    notable_works = []
    songs = []
    albums = []

    entities_info = request_el_wp_entities(person, utterance)
    for entity_label in entities_info:
        triplets = entities_info[entity_label]

        occupations = triplets["occupation"]
        occupation_titles = set([occ_title for occ_id, occ_title in occupations])
        if {"actor", "film actor", "television actor"}.intersection(occupation_titles):
            films_obtained = triplets.get("films of actor", [])

            films.append(films_obtained)

        if {"singer", "songwriter", "composer"}.intersection(occupation_titles):
            songs_obtained = triplets.get("songs", [])
            albums_obtained = triplets.get("albums", [])

            songs.append(songs_obtained)
            albums.append(albums_obtained)

        if {"writer", "poet", "novelist", "playwright"}.intersection(occupation_titles):
            notable_works_obtained = triplets.get("notable work", [])

            notable_works.append(notable_works_obtained)

        # if {"athlete"}.intersection(occupation_titles):
        #     sport = triplets.get("sport", [])
        #     teams = triplets.get("member of sports team", [])
        #     print("sport", sport)
        #     print("teams", teams)
        # if {"entrepreneur"}.intersection(occupation_titles):
        #     companies = triplets.get("owner of", [])
        #     products = triplets.get("notable work", [])
        #     print("companies", companies)
        #     print("products", products)
        # if {"politician", "statesperson"}.intersection(occupation_titles):
        #     country = triplets.get("country", [])
        #     parties = triplets.get("member of political party", [])
        #     print("country", country)
        #     print("parties", parties)

        # print(occupations)

    # returning our treasure!
    return films, songs, albums, notable_works


def get_top_people_from_wiki_for_cobot_topic(cobot_topic, top_people):
    raw_occupations_list = common_gossip.COBOT_TOPICS_TO_WIKI_OCCUPATIONS[cobot_topic]

    processed_occupations_tuple = tuple([occupation_item[1] for occupation_item in raw_occupations_list])
    results = custom_requests.request_triples_wikidata("find_top_people", [processed_occupations_tuple])
    results = results[0] if results else results
    if results:
        # if person is actually a ['Wikidata_ID', 'Display_Name']
        return [person_item[1] for person_item in results[0][0] if person_item]
    else:
        return []


def get_cobot_topic_for_occupation(occupation):
    all_topics_mappings = common_gossip.COBOT_TOPICS_TO_WIKI_OCCUPATIONS
    for topic, occupations in all_topics_mappings.items():
        for occupation_pair in occupations:
            occupation_name = occupation_pair[1]
            # not "in" but "equals"
            if str(occupation).lower() == str(occupation_name).lower():
                return topic

    return None


###

###


def get_not_used_and_save_reaction_to_new_mentioned_person(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    last_reactions_to_new_person = shared_memory.get("last_reactions_to_new_person", [])

    reaction = common_utils.get_not_used_template(
        used_templates=last_reactions_to_new_person, all_templates=this_gossip.OPINION_TO_USER_MENTIONING_SOMEONE_NEW
    )

    used_reacts = last_reactions_to_new_person + [reaction]
    state_utils.save_to_shared_memory(vars, last_reactions_to_new_person=used_reacts[-2:])
    return reaction


# def get_not_used_and_save_wait_but_why_question(vars):
#     shared_memory = state_utils.get_shared_memory(vars)
#     last_wait_but_why_questions = shared_memory.get("last_wait_but_why_questions", [])
#
#     question = common_utils.get_not_used_template(
#         used_templates=last_wait_but_why_questions, all_templates=this_gossip.WAIT_BUT_WHY_QUESTIONS
#     )
#
#     used_questions = last_wait_but_why_questions + [question]
#     state_utils.save_to_shared_memory(vars, last_reactions_to_new_person=used_questions[-2:])
#     return question


##################################################################################################################
# speech functions
##################################################################################################################


def get_speech_function_for_human_utterance(human_utterance):
    sf_type = human_utterance["annotations"].get("speech_function_classifier", {}).get("type", "")
    sf_confidence = human_utterance["annotations"].get("speech_function_classifier", {}).get("confidence", 0.0)
    return sf_type, sf_confidence


def get_speech_function_predictions_for_human_utterance(human_utterance):
    predicted_sfs = human_utterance["annotations"].get("speech_function_predictor", [])

    return predicted_sfs


def filter_speech_function_predictions_for_human_utterance(predicted_sfs):
    filtered_sfs = [sf_item for sf_item in predicted_sfs if "Open" not in sf_item]
    return filtered_sfs


patterns_agree = [
    "Support.Reply.Accept",
    "Support.Reply.Agree",
    "Support.Reply.Comply",
    "Support.Reply.Acknowledge",
    "Support.Reply.Affirm",
]
agree_patterns_re = re.compile("(" + "|".join(patterns_agree) + ")", re.IGNORECASE)


def is_speech_function_agree(vars):
    # fallback to MIDAS
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(agree_patterns_re, sf_type))
    # fallback to MIDAS
    flag = flag or is_midas_positive_answer(vars)
    # fallback to yes/no intents
    flag = flag or common_utils.is_yes(human_utterance)

    flag = flag and not is_not_interested_speech_function(vars)
    return flag


patterns_disagree = [
    "Support.Reply.Decline",
    "Support.Reply.Disagree",
    "Support.Reply.Non-comply",
    "Support.Reply.Withold",
    "Support.Reply.Disawow",
    "Support.Reply.Conflict",
]
disagree_patterns_re = re.compile("(" + "|".join(patterns_disagree) + ")", re.IGNORECASE)


def is_speech_function_disagree(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(disagree_patterns_re, sf_type))
    # fallback to MIDAS
    flag = flag or is_midas_negative_answer(vars)
    # fallback to yes/no intents
    flag = flag or common_utils.is_no(human_utterance)

    flag = flag and not is_not_interested_speech_function(vars)
    return flag


patterns_express_opinion = [
    "Initiate.Give.Opinion",
]
express_opinion_patterns_re = re.compile("(" + "|".join(patterns_express_opinion) + ")", re.IGNORECASE)


def is_cobot_opinion_expressed(vars):
    intents = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="all")
    opinion_expression_detected = "Opinion_ExpressionIntent" in intents
    return bool(opinion_expression_detected)


def is_cobot_opinion_demanded(vars):
    intents = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="all")
    opinion_request_detected = "Opinion_RequestIntent" in intents
    return bool(opinion_request_detected)


def is_speech_function_express_opinion(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(express_opinion_patterns_re, sf_type))
    # fallback to MIDAS
    flag = flag or is_midas_opinion_expression(vars)
    # # fallback to CoBot intents
    flag = flag or is_cobot_opinion_expressed(vars)
    flag = flag or common_utils.is_no(human_utterance)
    # bug check (sometimes opinion by MIDAS can be incorrectly detected in a simple yes/no answer from user)
    flag = flag and not common_utils.is_no(human_utterance) and not common_utils.is_yes(human_utterance)
    return flag


patterns_demand_opinion = [
    "Initiate.Demand.Opinion",
]
demand_opinion_patterns_re = re.compile("(" + "|".join(patterns_demand_opinion) + ")", re.IGNORECASE)


def is_speech_function_demand_opinion(vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    sf_type, sf_confidence = get_speech_function_for_human_utterance(human_utterance)
    flag = sf_type and bool(re.search(demand_opinion_patterns_re, sf_type))
    # # fallback to CoBot intents
    flag = flag or is_cobot_opinion_demanded(vars)
    flag = flag or common_utils.is_no(human_utterance)
    # bug check (sometimes opinion by MIDAS can be incorrectly detected in a simple yes/no answer from user)
    flag = flag and not common_utils.is_no(human_utterance) and not common_utils.is_yes(human_utterance)
    return flag


def get_mentioned_people(vars):
    user_mentioned_named_entities = state_utils.get_named_entities_from_human_utterance(vars)
    user_mentioned_names = []

    logger.info("user_mentioned_named_entities: " + str(user_mentioned_named_entities))

    for named_entity in user_mentioned_named_entities:
        logger.debug(f"named entity: {named_entity}")
        if named_entity["type"] == "PER":
            user_mentioned_names.append(named_entity["text"])
    return user_mentioned_names


def get_mentioned_orgs(vars):
    user_mentioned_named_entities = state_utils.get_named_entities_from_human_utterance(vars)
    user_mentioned_names = []
    for named_entity in user_mentioned_named_entities:
        if named_entity["type"] == "ORG":
            user_mentioned_names.append(named_entity["text"])
    return user_mentioned_names


# def get_mentioned_people(vars, cobot_topic):
#     # obtaining named entities
#     named_entities = state_utils.get_named_entities_from_human_utterance(vars)

#     # human_utterance = state_utils.get_last_human_utterance(vars)

#     # basic_celebrities_list = ['Q33999',  # actor
#     #                        "Q10800557",  # film actor
#     #                        "Q10798782",  # television actor
#     #                        "Q2405480",  # voice actor
#     #                        'Q17125263',  # youtuber
#     #                        'Q245068',  # comedian
#     #                        'Q2066131',  # sportsman
#     #                        'Q947873',  # television presenter
#     #                        'Q2405480',  # comedian
#     #                        'Q211236',  # celebrity
#     #                        'Q177220']  # singer

#     # professions_for_cobot_topic =

#     # celebrity_name, celebrity_type, celebrity_raw_type = state_utils.get_types_from_annotations(
#     #     human_utterance['annotations'], tocheck_relation='occupation',
#     #     types=raw_profession_list, exclude_types=[])

#     logger.debug("detected entities: " + str(named_entities))

#     return False


##################################################################################################################
# more specific intents
##################################################################################################################


patterns_not_interested = [
    "not interested",
    "don't care",
    "move on",
    "skip",
    "cancel",
    "avoid",
    "not into",
    "not really into",
    "no interest for me",
    "I don't bother",
    "don't really want to talk about this",
    "don't feel comfortable discussing this",
    "We’d better not to enter this subject",
    "I'd rather not go there right now",
    "have no interest in discussing that",
    "What an idiotic topic of conversation",
    "That subject really bothers me and I don't want to talk about it",
    "Can we talk about something else",
    "Must we discuss this",
    "Can we discuss this later",
]
patterns_not_interested_re = re.compile("(" + "|".join(patterns_not_interested) + ")", re.IGNORECASE)


def is_not_interested_speech_function(vars):
    human_text = state_utils.get_last_human_utterance(vars)["text"]

    flag = bool(re.search(patterns_not_interested_re, human_text))

    return flag


##################################################################################################################
# MIDAS
##################################################################################################################


def is_midas_positive_answer(vars):
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")

    intent_detected = any([intent in midas_classes for intent in ["pos_answer"]])

    return intent_detected


def is_midas_negative_answer(vars):
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")

    intent_detected = any([intent in midas_classes for intent in ["neg_answer"]])

    return intent_detected


def is_midas_opinion_expression(vars):
    midas_classes = common_utils.get_intents(state_utils.get_last_human_utterance(vars), which="midas")
    intent_detected = any([intent in midas_classes for intent in ["opinion"]])

    return intent_detected


##################################################################################################################
# occupation
##################################################################################################################


def get_basic_occupation_for_topic(cobot_topic):
    occupations = [x["Occupation"] for x in this_gossip.TOPICS_TO_OCCUPATIONS if x["Topic"] == cobot_topic]
    if occupations:
        return occupations[0]


def get_occupation_for_person(person, topic, utterance):
    # obtaining basic occupation
    basic_occupation = get_basic_occupation_for_topic(topic)
    occupation = basic_occupation if basic_occupation else "person"
    logger.debug(f"basic occupation: {occupation}")

    # trying to get a better thing from Wiki
    occupations = get_occupations_for_person_from_wiki_parser(person, utterance)
    new_occupation = occupations and len(occupations[0]) > 1 and len(occupations[0][1]) > 1 and occupations[0][1][1]
    occupation = new_occupation if new_occupation else occupation

    return occupation
