import logging
import os
import random

from df_engine.core import Context, Actor

import common.constants as common_constants
import common.link as common_link
import common.news as common_news
import common.utils as common_utils

logger = logging.getLogger(__name__)
SERVICE_NAME = os.getenv("SERVICE_NAME")


NEWS_API_ANNOTATOR_URL = os.getenv("NEWS_API_ANNOTATOR_URL")


def get_new_human_labeled_noun_phrase(ctx: Context, actor: Actor) -> list:
    return (
        []
        if ctx.validation
        else (get_last_human_utterance(ctx, actor).get("annotations", {}).get("cobot_entities", {}).get("entities", []))
    )


def get_human_sentiment(ctx: Context, actor: Actor, negative_threshold=0.5, positive_threshold=0.333) -> str:
    sentiment_probs = (
        None if ctx.validation else common_utils.get_sentiment(get_last_human_utterance(ctx, actor), probs=True)
    )
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


def get_cross_state(ctx: Context, actor: Actor, service_name=SERVICE_NAME.replace("-", "_")) -> dict:
    return {} if ctx.validation else ctx.misc["agent"]["dff_shared_state"]["cross_states"].get(service_name, {})


def save_cross_state(ctx: Context, actor: Actor, service_name=SERVICE_NAME.replace("-", "_"), new_state={}):
    if not ctx.validation:
        ctx.misc["agent"]["dff_shared_state"]["cross_states"][service_name] = new_state


def get_cross_link(ctx: Context, actor: Actor, service_name=SERVICE_NAME.replace("-", "_")) -> dict:
    links = {} if ctx.validation else ctx.misc["agent"]["dff_shared_state"]["cross_links"].get(service_name, {})
    cur_human_index = get_human_utter_index(ctx, actor)
    cross_link = [cross_link for human_index, cross_link in links.items() if (cur_human_index - int(human_index)) == 1]
    cross_link = cross_link[0] if cross_link else {}
    return cross_link


def set_cross_link(
    ctx: Context,
    actor: Actor,
    to_service_name,
    cross_link_additional_data={},
    from_service_name=SERVICE_NAME.replace("-", "_"),
):
    cur_human_index = get_human_utter_index(ctx, actor)
    if not ctx.validation:
        ctx.misc["agent"]["dff_shared_state"]["cross_links"][to_service_name] = {
            cur_human_index: {
                "from_service": from_service_name,
                **cross_link_additional_data,
            }
        }


def reset_response_parts(ctx: Context, actor: Actor):
    if not ctx.validation and "response_parts" in ctx.misc["agent"]:
        del ctx.misc["agent"]["response_parts"]


def add_parts_to_response_parts(ctx: Context, actor: Actor, parts=[]):
    response_parts = set([] if ctx.validation else ctx.misc["agent"].get("response_parts", []))
    response_parts.update(parts)
    if not ctx.validation:
        ctx.misc["agent"]["response_parts"] = sorted(list(response_parts))


def set_acknowledgement_to_response_parts(ctx: Context, actor: Actor):
    reset_response_parts(ctx, actor)
    add_parts_to_response_parts(ctx, actor, parts=["acknowledgement"])


def add_acknowledgement_to_response_parts(ctx: Context, actor: Actor):
    if not ctx.validation and ctx.misc["agent"].get("response_parts") is None:
        add_parts_to_response_parts(ctx, actor, parts=["body"])
    add_parts_to_response_parts(ctx, actor, parts=["acknowledgement"])


def set_body_to_response_parts(ctx: Context, actor: Actor):
    reset_response_parts(ctx, actor)
    add_parts_to_response_parts(ctx, actor, parts=["body"])


def add_body_to_response_parts(ctx: Context, actor: Actor):
    add_parts_to_response_parts(ctx, actor, parts=["body"])


def set_prompt_to_response_parts(ctx: Context, actor: Actor):
    reset_response_parts(ctx, actor)
    add_parts_to_response_parts(ctx, actor, parts=["prompt"])


def add_prompt_to_response_parts(ctx: Context, actor: Actor):
    add_parts_to_response_parts(ctx, actor, parts=["prompt"])


def get_shared_memory(ctx: Context, actor: Actor) -> dict:
    return {} if ctx.validation else ctx.misc["agent"]["shared_memory"]


def get_used_links(ctx: Context, actor: Actor) -> dict:
    return {} if ctx.validation else ctx.misc["agent"]["used_links"]


def get_age_group(ctx: Context, actor: Actor) -> dict:
    return {} if ctx.validation else ctx.misc["agent"]["age_group"]


def set_age_group(ctx: Context, actor: Actor, set_age_group):
    if not ctx.validation:
        ctx.misc["agent"]["age_group"] = set_age_group


def get_disliked_skills(ctx: Context, actor: Actor) -> list:
    return [] if ctx.validation else ctx.misc["agent"]["disliked_skills"]


def get_human_utter_index(ctx: Context, actor: Actor) -> int:
    return 0 if ctx.validation else ctx.misc["agent"]["human_utter_index"]


def get_previous_human_utter_index(ctx: Context, actor: Actor) -> int:
    return 0 if ctx.validation else ctx.misc["agent"]["previous_human_utter_index"]


def get_dialog(ctx: Context, actor: Actor) -> dict:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]


def get_human_utterances(ctx: Context, actor: Actor) -> dict:
    return [] if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]


def get_last_human_utterance(ctx: Context, actor: Actor) -> dict:
    return {"text": "", "annotations": {}} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"][-1]


def get_bot_utterances(ctx: Context, actor: Actor) -> list:
    return [] if ctx.validation else ctx.misc["agent"]["dialog"]["bot_utterances"]


def get_last_bot_utterance(ctx: Context, actor: Actor) -> dict:
    if not ctx.validation and ctx.misc["agent"]["dialog"]["bot_utterances"]:
        return ctx.misc["agent"]["dialog"]["bot_utterances"][-1]
    else:
        return {"text": "", "annotations": {}}


def save_to_shared_memory(ctx: Context, actor: Actor, **kwargs):
    if not ctx.validation:
        ctx.misc["agent"]["shared_memory"].update(kwargs)


def update_used_links(ctx: Context, actor: Actor, linked_skill_name, linking_phrase):
    if not ctx.validation:
        agent = ctx.misc["agent"]
        agent["used_links"][linked_skill_name] = agent["used_links"].get(linked_skill_name, []) + [linking_phrase]


def get_new_link_to(ctx: Context, actor: Actor, skill_names):
    used_links = get_used_links(ctx, actor)
    disliked_skills = get_disliked_skills(ctx, actor)

    link = common_link.link_to(
        skill_names, human_attributes={"used_links": used_links, "disliked_skills": disliked_skills}
    )
    update_used_links(ctx, actor, link["skill"], link["phrase"])
    return link


def set_dff_suspension(ctx: Context, actor: Actor):
    if not ctx.validation:
        ctx.misc["agent"]["current_turn_dff_suspended"] = True


def reset_dff_suspension(ctx: Context, actor: Actor):
    if not ctx.validation:
        ctx.misc["agent"]["current_turn_dff_suspended"] = False


def set_confidence(ctx: Context, actor: Actor, confidence=1.0):
    if not ctx.validation:
        ctx.misc["agent"]["response"].update({"confidence": confidence})
    if confidence == 0.0:
        reset_can_continue(ctx, actor)


def set_can_continue(ctx: Context, actor: Actor, continue_flag=common_constants.CAN_CONTINUE_SCENARIO):
    if not ctx.validation:
        ctx.misc["agent"]["response"].update({"can_continue": continue_flag})


def reset_can_continue(ctx: Context, actor: Actor):
    if not ctx.validation and "can_continue" in ctx.misc["agent"]["response"]:
        del ctx.misc["agent"]["response"]["can_continue"]


def get_named_entities_from_human_utterance(ctx: Context, actor: Actor):
    # ent is a dict! ent = {"text": "London":, "type": "LOC"}
    entities = common_utils.get_entities(
        get_last_human_utterance(ctx, actor),
        only_named=True,
        with_labels=True,
    )
    return entities


def get_nounphrases_from_human_utterance(ctx: Context, actor: Actor):
    nps = common_utils.get_entities(
        get_last_human_utterance(ctx, actor),
        only_named=False,
        with_labels=False,
    )
    return nps


def get_fact_random_annotations_from_human_utterance(ctx: Context, actor: Actor) -> dict:
    if not ctx.validation:
        return (
            get_last_human_utterance(ctx, actor)
            .get("annotations", {})
            .get("fact_random", {"facts": [], "response": ""})
        )
    else:
        return {"facts": [], "response": ""}


def get_fact_for_particular_entity_from_human_utterance(ctx: Context, actor: Actor, entity) -> list:
    fact_random_results = get_fact_random_annotations_from_human_utterance(ctx, actor)
    facts_for_entity = []
    for fact in fact_random_results.get("facts", []):
        is_same_entity = fact.get("entity_substr", "").lower() == entity.lower()
        is_sorry = "Sorry, I don't know" in fact.get("fact", "")
        if is_same_entity and not is_sorry:
            facts_for_entity += [fact["fact"]]

    return facts_for_entity


def get_news_about_particular_entity_from_human_utterance(ctx: Context, actor: Actor, entity) -> dict:
    last_uttr = get_last_human_utterance(ctx, actor)
    last_uttr_entities_news = last_uttr.get("annotations", {}).get("news_api_annotator", [])
    curr_news = {}
    for news_entity in last_uttr_entities_news:
        if news_entity["entity"] == entity:
            curr_news = news_entity["news"]
            break
    if not curr_news:
        curr_news = common_news.get_news_about_topic(entity, NEWS_API_ANNOTATOR_URL)

    return curr_news


def get_facts_from_fact_retrieval(ctx: Context, actor: Actor) -> list:
    annotations = get_last_human_utterance(ctx, actor).get("annotations", {})
    if "fact_retrieval" in annotations:
        if isinstance(annotations["fact_retrieval"], dict):
            return annotations["fact_retrieval"].get("facts", [])
        elif isinstance(annotations["fact_retrieval"], list):
            return annotations["fact_retrieval"]
    return []


def get_unrepeatable_index_from_rand_seq(
    ctx: Context, actor: Actor, seq_name, seq_max, renew_seq_if_empty=False
) -> int:
    """Return a unrepeatable index from RANDOM_SEQUENCE.
    RANDOM_SEQUENCE is stored in shared merory by name `seq_name`.
    RANDOM_SEQUENCE is shuffled [0..`seq_max`].
    RANDOM_SEQUENCE will be updated after index will get out of RANDOM_SEQUENCE if `renew_seq_if_empty` is True
    """
    shared_memory = get_shared_memory(ctx, actor)
    seq = shared_memory.get(seq_name, random.sample(list(range(seq_max)), seq_max))
    if renew_seq_if_empty or seq:
        seq = seq if seq else random.sample(list(range(seq_max)), seq_max)
        next_index = seq[-1] if seq else None
        save_to_shared_memory(ctx, **{seq_name: seq[:-1]})
        return next_index


def get_history(ctx: Context, actor: Actor):
    if not ctx.validation:
        return ctx.misc["agent"]["history"]
    return {}


def get_n_last_state(ctx: Context, actor: Actor, n) -> str:
    last_state = ""
    history = list(get_history(ctx, actor).items())
    if history:
        history_sorted = sorted(history, key=lambda x: x[0])
        if len(history_sorted) >= n:
            last_state = history_sorted[-n][1]
    return last_state


def get_last_state(ctx: Context, actor: Actor) -> str:
    last_state = ""
    history = list(get_history(ctx, actor).items())
    if history:
        history_sorted = sorted(history, key=lambda x: x[0])
        last_state = history_sorted[-1][1]
    return last_state


def add_smth_to_response_attributes(ctx: Context, actor: Actor, smth_key=None, smth_value=None):
    if not ctx.validation and not (smth_key is None or smth_value is None):
        ctx.misc["agent"]["response"].update({smth_key: smth_value})


def get_dialog_id(ctx: Context, actor: Actor) -> dict:
    return "unknown" if ctx.validation else ctx.misc["agent"]["dialog_id"]
