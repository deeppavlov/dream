import logging
import re
import nltk
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes
from common.wiki_skill import find_entity_by_types
from dff import Context, Actor, Node

logger = logging.getLogger(__name__)


def how_to_draw_response(ctx: Context, actor: Actor, *args, **kwargs):
    response = "Would you like to know how to improve your drawing skills?"
    return response


def set_confidence_and_continue_flag(confidence, continue_flag):
    def set_function(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
        shared_memory = ctx.shared_memory
        shared_memory["confidence"] = confidence
        shared_memory["continue_flag"] = continue_flag
        ctx.shared_memory = shared_memory
        return node_label, node

    return set_function


def drawing_request(ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    vars = ctx.shared_memory.get("vars", {})
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
    def has_entities_func(ctx):
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
    def check_speech_function(ctx: Context, actor: Actor, *args, **kwargs):
        flag = False
        vars = ctx.shared_memory.get("vars", {})
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


def slot_filling(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    response = node.response
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
    node.response = " ".join(resp_list)
    return node_label, node


def extract_album(ctx: Context):
    slot_values = ctx.shared_memory.get("slot_values", {})
    albums = ["Please Please Me", "With the Beatles", "Introducing... The Beatles", "Meet the Beatles!",
              "Twist and Shout", "The Beatles' Second Album", "The Beatles' Long Tall Sally", "A Hard Day's Night",
              "Something New", "Help!", "Sgt. Pepper's Lonely Hearts Club Band", "White Album", "The Beatles Beat",
              "Another Beatles Christmas Record", "Beatles '65", "Beatles VI", "Five Nights In A Judo Arena",
              "The Beatles at the Hollywood Bowl", "Live! at the Star-Club in Hamburg, German; 1962",
              "The Black Album", "20 Exitos De Oro", "A Doll's House", "The Complete Silver Beatles",
              "Rock 'n' Roll Music Vol. 1", "Yellow Submarine", "Let It Be", "Beatles for Sale",
              "Revolver", "Abbey Road", "Rubber Soul"]
    albums_re = "|".join(albums)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_album = re.findall(albums_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_album:
        slot_values["beatles_album"] = extracted_album[0]
        ctx.shared_memory["slot_values"] = slot_values
        return extracted_album[0]

    else:
        return ""


def has_album():
    return True


def has_video(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    videos = ["Hey Jude", "Don't Let Me Down", "We Can Work it Out", "Come Together",
              "Yellow Submarine", "Revolution", "Imagine", "Something", "Hello, Goodbye",
              "A Day In The Life", "Help!", "Penny Lane"]

    videos_re = "|".join(videos)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_videos = re.findall(videos_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_videos:
        return True
    return False


def extract_video(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    videos = ["Hey Jude", "Don't Let Me Down", "We Can Work it Out", "Come Together",
              "Yellow Submarine", "Revolution", "Imagine", "Something", "Hello, Goodbye",
              "A Day In The Life", "Help!", "Penny Lane"]
    videos_re = "|".join(videos)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_videos = re.findall(videos_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_videos:
        slot_values["song_video"] = extracted_videos[0]
        ctx.shared_memory["slot_values"] = slot_values

    return node_label, node
