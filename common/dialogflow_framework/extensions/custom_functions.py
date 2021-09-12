import logging
import re
import nltk
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes
from common.wiki_skill import find_entity_by_types

logger = logging.getLogger(__name__)


def how_to_draw_response(vars):
    response = "Would you like to know how to improve your drawing skills?"
    return response


def drawing_request(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isyes = is_yes(user_uttr)
    if re.findall("do you like drawing", bot_uttr.get("text", "")) and isyes:
        flag = True
    return flag


def extract_entity(ctx, entity_type):
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr.get("annotations", {})
    logger.info(f"annotations {annotations}")
    if entity_type.startswith("tags"):
        tag = entity_type.split("tags:")[1]
        nounphrases = annotations.get("entity_detection", {}).get("labelled_entities", [])
        for nounphr in nounphrases:
            nounphr_text = nounphr.get("text", "")
            nounphr_label = nounphr.get("label", "")
            if nounphr_label == tag:
                found_entity = nounphr_text
                return found_entity
    elif entity_type.startswith("wiki"):
        wp_type = entity_type.split("wiki:")[1]
        found_entity, *_ = find_entity_by_types(annotations, [wp_type])
        if found_entity:
            return found_entity
    elif entity_type == "any_entity":
        entities = annotations.get("entity_detection", {}).get("entities", [])
        if entities:
            return entities[0]
    else:
        res = re.findall(entity_type, user_uttr["text"])
        if res:
            return res[0]
    return ""


def has_entities(entity_types):
    def has_entities_func(ctx: Context, actor: Actor, *args, **kwargs):
        flag = False
        if isinstance(entity_types, str):
            extracted_entity = extract_entity(ctx, entity_types)
            if extracted_entity:
                flag = True
        elif isinstance(entity_types, list):
            for entity_type in entity_types:
                extracted_entity = extract_entity(ctx, entity_type)
                if extracted_entity:
                    flag = True
                    break
        return flag

    return has_entities_func


def entities(**kwargs):
    slot_info = list(kwargs.items())

    def extract_entities(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
        slot_values = ctx.shared_memory.get("slot_values", {})
        for slot_name, slot_types in slot_info:
            if isinstance(slot_types, str):
                extracted_entity = extract_entity(ctx, slot_types)
                if extracted_entity:
                    slot_values[slot_name] = extracted_entity
                    ctx.shared_memory["slot_values"] = slot_values
            elif isinstance(slot_types, list):
                for slot_type in slot_types:
                    extracted_entity = extract_entity(ctx, slot_type)
                    if extracted_entity:
                        slot_values[slot_name] = extracted_entity
                        ctx.shared_memory["slot_values"] = slot_values
        return node_label, node

    return extract_entities


def speech_functions(*args):
    def check_speech_function(vars):
        flag = False
        user_uttr = state_utils.get_last_human_utterance(vars)
        annotations = user_uttr["annotations"]
        speech_functions = set(annotations.get("speech_function_classifier", []))
        for elem in args:
            if (isinstance(elem, str) and elem in speech_functions) or (
                isinstance(elem, list) and set(elem).intersection(speech_functions)
            ):
                flag = True
        logger.info(f"check_speech_functions: {args}, {flag}")
        return flag

    return check_speech_function


def slot_filling(vars, response):
    shared_memory = state_utils.get_shared_memory(vars)
    slot_values = shared_memory.get("slots", {})
    utt_list = nltk.sent_tokenize(response)
    resp_list = []
    for utt in utt_list:
        utt_slots = re.findall(r"{(.*?)}", utt)
        for slot in utt_slots:
            slot_value = slot_values.get(slot, "")
            if slot_value:
                slot_repl = "{" + slot + "}"
                utt = utt.replace(slot_repl, slot_value)
        if "{" not in utt:
            resp_list.append(utt)
    response = " ".join(resp_list)
    return response
