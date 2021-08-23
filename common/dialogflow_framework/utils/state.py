import logging
import os
import random

import common.constants as common_constants
import common.news as common_news
import common.utils as common_utils
import common.link as common_link

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
SERVICE_NAME = os.getenv("SERVICE_NAME")


#  vars is described in README.md
NEWS_API_ANNOTATOR_URL = os.getenv("NEWS_API_ANNOTATOR_URL")


def get_new_human_labeled_noun_phrase(vars):
    return (
        vars["agent"]["dialog"]["human_utterances"][-1]
        .get("annotations", {})
        .get("cobot_entities", {})
        .get("entities", [])
    )


def get_human_sentiment(vars, negative_threshold=0.5, positive_threshold=0.333):
    sentiment_probs = common_utils.get_sentiment(vars["agent"]["dialog"]["human_utterances"][-1], probs=True)
    if sentiment_probs and isinstance(sentiment_probs, dict):
        max_sentiment_prob = max(sentiment_probs.values())
        max_sentiments = [
            sentiment for sentiment in sentiment_probs if sentiment_probs[sentiment] == max_sentiment_prob
        ]
        if max_sentiments:
            max_sentiment = max_sentiments[0]
            return_negative = max_sentiment == "negative" and max_sentiment_prob >= negative_threshold
            return_positive = max_sentiment == "positive" and max_sentiment_prob >= positive_threshold
            if return_negative or return_positive:
                return max_sentiment
    return "neutral"


def get_cross_state(vars, service_name=SERVICE_NAME.replace("-", "_")):
    return vars["agent"]["dff_shared_state"]["cross_states"].get(service_name, {})


def save_cross_state(vars, service_name=SERVICE_NAME.replace("-", "_"), new_state={}):
    vars["agent"]["dff_shared_state"]["cross_states"][service_name] = new_state


def get_cross_link(vars, service_name=SERVICE_NAME.replace("-", "_")):
    links = vars["agent"]["dff_shared_state"]["cross_links"].get(service_name, {})
    cur_human_index = get_human_utter_index(vars)
    cross_link = [cross_link for human_index, cross_link in links.items() if (cur_human_index - int(human_index)) == 1]
    cross_link = cross_link[0] if cross_link else {}
    return cross_link


def set_cross_link(
    vars,
    to_service_name,
    cross_link_additional_data={},
    from_service_name=SERVICE_NAME.replace("-", "_"),
):
    cur_human_index = get_human_utter_index(vars)
    vars["agent"]["dff_shared_state"]["cross_links"][to_service_name] = {
        cur_human_index: {
            "from_service": from_service_name,
            **cross_link_additional_data,
        }
    }


def reset_response_parts(vars):
    if "response_parts" in vars["agent"]:
        del vars["agent"]["response_parts"]


def add_parts_to_response_parts(vars, parts=[]):
    response_parts = set(vars["agent"].get("response_parts", []))
    response_parts.update(parts)
    vars["agent"]["response_parts"] = list(response_parts)


def set_acknowledgement_to_response_parts(vars):
    reset_response_parts(vars)
    add_parts_to_response_parts(vars, parts=["acknowledgement"])


def add_acknowledgement_to_response_parts(vars):
    if vars["agent"].get("response_parts") is None:
        add_parts_to_response_parts(vars, parts=["body"])
    add_parts_to_response_parts(vars, parts=["acknowledgement"])


def set_body_to_response_parts(vars):
    reset_response_parts(vars)
    add_parts_to_response_parts(vars, parts=["body"])


def add_body_to_response_parts(vars):
    add_parts_to_response_parts(vars, parts=["body"])


def set_prompt_to_response_parts(vars):
    reset_response_parts(vars)
    add_parts_to_response_parts(vars, parts=["prompt"])


def add_prompt_to_response_parts(vars):
    add_parts_to_response_parts(vars, parts=["prompt"])


def get_shared_memory(vars):
    return vars["agent"]["shared_memory"]


def get_used_links(vars):
    return vars["agent"]["used_links"]


def get_age_group(vars):
    return vars["agent"]["age_group"]


def set_age_group(vars, set_age_group):
    vars["agent"]["age_group"] = set_age_group


def get_disliked_skills(vars):
    return vars["agent"]["disliked_skills"]


def get_human_utter_index(vars):
    return vars["agent"]["human_utter_index"]


def get_previous_human_utter_index(vars):
    return vars["agent"]["previous_human_utter_index"]


def get_dialog(vars):
    return vars.get("agent", {}).get("dialog", {"human_utterances": []})


def get_last_human_utterance(vars):
    return vars.get("agent", {}).get("dialog", {}).get("human_utterances", [{"text": "", "annotations": {}}])[-1]


def get_bot_utterances(vars):
    return vars.get("agent", {}).get("dialog", {}).get("bot_utterances", [])


def get_last_bot_utterance(vars):
    if vars.get("agent", {}).get("dialog", {}).get("bot_utterances", [{"text": "", "annotations": {}}]):
        return vars.get("agent", {}).get("dialog", {}).get("bot_utterances", [{"text": "", "annotations": {}}])[-1]
    else:
        return {"text": "", "annotations": {}}


def save_to_shared_memory(vars, **kwargs):
    vars["agent"]["shared_memory"].update(kwargs)


def update_used_links(vars, linked_skill_name, linking_phrase):
    agent = vars["agent"]
    agent["used_links"][linked_skill_name] = agent["used_links"].get(linked_skill_name, []) + [linking_phrase]


def get_new_link_to(vars, skill_names):
    used_links = get_used_links(vars)
    disliked_skills = get_disliked_skills(vars)

    link = common_link.link_to(
        skill_names, human_attributes={"used_links": used_links, "disliked_skills": disliked_skills}
    )
    update_used_links(vars, link["skill"], link["phrase"])
    return link


def set_dff_suspension(vars):
    vars["agent"]["current_turn_dff_suspended"] = True


def reset_dff_suspension(vars):
    vars["agent"]["current_turn_dff_suspended"] = False


def set_confidence(vars, confidence=1.0):
    vars["agent"]["response"].update({"confidence": confidence})
    if confidence == 0.0:
        reset_can_continue(vars)


def set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO):
    vars["agent"]["response"].update({"can_continue": continue_flag})


def reset_can_continue(vars):
    if "can_continue" in vars["agent"]["response"]:
        del vars["agent"]["response"]["can_continue"]


def get_named_entities_from_human_utterance(vars):
    # ent is a dict! ent = {"text": "London":, "type": "LOC"}
    entities = common_utils.get_entities(
        vars["agent"]["dialog"]["human_utterances"][-1], only_named=True, with_labels=True
    )
    return entities


def get_nounphrases_from_human_utterance(vars):
    nps = common_utils.get_entities(
        vars["agent"]["dialog"]["human_utterances"][-1], only_named=False, with_labels=False
    )
    return nps


def get_cobotqa_annotations_from_human_utterance(vars):
    return (
        vars["agent"]["dialog"]["human_utterances"][-1]
        .get("annotations", {})
        .get("cobotqa_annotator", {"facts": [], "response": ""})
    )


def get_fact_for_particular_entity_from_human_utterance(vars, entity):
    cobotqa_annotations = get_cobotqa_annotations_from_human_utterance(vars)
    facts_for_entity = []
    for fact in cobotqa_annotations["facts"]:
        if fact.get("entity", "").lower() == entity.lower() and "Sorry, I don't know" not in fact.get("fact", ""):
            facts_for_entity += [fact["fact"]]

    return facts_for_entity


def get_news_about_particular_entity_from_human_utterance(vars, entity):
    last_uttr = get_last_human_utterance(vars)
    last_uttr_entities_news = last_uttr.get("annotations", {}).get("news_api_annotator", [])
    curr_news = {}
    for news_entity in last_uttr_entities_news:
        if news_entity["entity"] == entity:
            curr_news = news_entity["news"]
            break
    if not curr_news:
        curr_news = common_news.get_news_about_topic(entity, NEWS_API_ANNOTATOR_URL)

    return curr_news


def get_facts_from_fact_retrieval(vars):
    annotations = vars["agent"]["dialog"]["human_utterances"][-1].get("annotations", {})
    if "fact_retrieval" in annotations:
        if isinstance(annotations["fact_retrieval"], dict):
            return annotations["fact_retrieval"].get("facts", [])
        elif isinstance(annotations["fact_retrieval"], list):
            return annotations["fact_retrieval"]
    return []


def get_unrepeatable_index_from_rand_seq(vars, seq_name, seq_max, renew_seq_if_empty=False):
    """Return a unrepeatable index from RANDOM_SEQUENCE.
    RANDOM_SEQUENCE is stored in shared merory by name `seq_name`.
    RANDOM_SEQUENCE is shuffled [0..`seq_max`].
    RANDOM_SEQUENCE will be updated after index will get out of RANDOM_SEQUENCE if `renew_seq_if_empty` is True
    """
    shared_memory = get_shared_memory(vars)
    seq = shared_memory.get(seq_name, random.sample(list(range(seq_max)), seq_max))
    if renew_seq_if_empty or seq:
        seq = seq if seq else random.sample(list(range(seq_max)), seq_max)
        next_index = seq[-1] if seq else None
        save_to_shared_memory(vars, **{seq_name: seq[:-1]})
        return next_index
