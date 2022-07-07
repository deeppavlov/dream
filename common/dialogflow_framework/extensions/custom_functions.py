import logging
import re
import nltk
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes

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
    slot_values = shared_memory.get("slot_values", {})
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
