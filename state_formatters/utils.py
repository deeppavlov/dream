from typing import Dict, List
import logging
from copy import deepcopy
import re

from common.universal_templates import if_lets_chat_about_topic
from common.utils import get_intents

logger = logging.getLogger(__name__)

LAST_N_TURNS = 5  # number of turns to consider in annotator/skill.


spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^a-zа-я0-9' ]", flags=re.IGNORECASE)


def clean_text(text):
    return special_symb_pat.sub(" ", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()


def get_last_n_turns(
        dialog: Dict,
        bot_last_turns=None,
        human_last_turns=None,
        total_last_turns=None,
        excluded_attributes=["entities"],
):
    bot_last_turns = bot_last_turns or LAST_N_TURNS
    human_last_turns = human_last_turns or bot_last_turns + 1
    total_last_turns = total_last_turns or bot_last_turns * 2 + 1

    new_dialog = {}
    for key, value in dialog.items():
        if key not in ["utterances", "human_utterances", "bot_utterances"]:
            if isinstance(value, dict) and "attributes" in value:
                new_dialog[key] = {k: deepcopy(v) for k, v in value.items() if k != "attributes"}
                new_dialog[key]["attributes"] = {
                    k: deepcopy(v) for k, v in value["attributes"].items() if k not in excluded_attributes
                }
            else:
                new_dialog[key] = deepcopy(value)
    new_dialog["utterances"] = deepcopy(dialog["utterances"][-total_last_turns:])

    new_dialog["human_utterances"] = []
    new_dialog["bot_utterances"] = []

    for utt in new_dialog["utterances"]:
        if utt["user"]["user_type"] == "human":
            new_dialog["human_utterances"].append(deepcopy(utt))
        elif utt["user"]["user_type"] == "bot":
            new_dialog["bot_utterances"].append(deepcopy(utt))

    return new_dialog


def is_human_uttr_repeat_request_or_misheard(utt):
    is_repeat_request = utt.get("annotations", {}).get("intent_catcher", {}).get("repeat", {}).get("detected", 0) == 1
    is_low_asr_conf = utt.get("annotations", {}).get("asr", {}).get("asr_confidence", "") == "very_low"
    if is_low_asr_conf or is_repeat_request:
        return True
    else:
        return False


def is_bot_uttr_repeated_or_misheard(utt):
    is_asr = utt.get("active_skill", "") == "misheard_asr" and utt.get("confidence", 0.0) == 1.0
    is_repeated = "#+#repeat" in utt.get("text", "")
    if is_asr or is_repeated:
        return True
    else:
        return False


def remove_clarification_turns_from_dialog(dialog):
    new_dialog = deepcopy(dialog)
    new_dialog["utterances"] = []
    dialog_length = len(dialog["utterances"])

    for i, utt in enumerate(dialog["utterances"]):
        if utt["user"]["user_type"] == "human":
            new_dialog["utterances"].append(utt)
        elif utt["user"]["user_type"] == "bot":
            if (
                    0 < i < dialog_length - 1
                    and is_bot_uttr_repeated_or_misheard(utt)
                    and is_human_uttr_repeat_request_or_misheard(dialog["utterances"][i - 1])
            ):
                new_dialog["utterances"] = new_dialog["utterances"][:-1]
            else:
                new_dialog["utterances"].append(utt)

    new_dialog["human_utterances"] = []
    new_dialog["bot_utterances"] = []

    for utt in new_dialog["utterances"]:
        if utt["user"]["user_type"] == "human":
            new_dialog["human_utterances"].append(deepcopy(utt))
        elif utt["user"]["user_type"] == "bot":
            new_dialog["bot_utterances"].append(deepcopy(utt))

    return new_dialog


def replace_with_annotated_utterances(dialog, mode="punct_sent"):
    if mode == "punct_sent":
        for utt in dialog["utterances"] + dialog["human_utterances"]:
            if "sentseg" in utt["annotations"]:
                utt["text"] = utt["annotations"]["sentseg"]["punct_sent"]
    elif mode == "segments":
        for utt in dialog["utterances"] + dialog["human_utterances"] + dialog["bot_utterances"]:
            if "sentseg" in utt["annotations"]:
                utt["text"] = deepcopy(utt["annotations"]["sentseg"]["segments"])
            elif isinstance(utt["text"], str):
                utt["text"] = [utt["text"]]
    elif mode == "modified_sents":
        for utt in dialog["utterances"] + dialog["human_utterances"]:
            if "sentrewrite" in utt["annotations"]:
                utt["text"] = utt["annotations"]["sentrewrite"]["modified_sents"][-1]
            elif "sentseg" in utt["annotations"]:
                utt["text"] = utt["annotations"]["sentseg"]["punct_sent"]
    elif mode == "clean_sent":
        for utt in dialog["utterances"] + dialog["human_utterances"] + dialog["bot_utterances"]:
            utt["text"] = clean_text(utt["text"])
    return dialog


def clean_up_utterances_to_avoid_unwanted_keys(
        dialog,
        wanted_keys=["text", "annotations", "active_skill"],
        types_utterances=["human_utterances", "bot_utterances", "utterances"],
):
    # Attention! It removes all other keys from the dialog
    new_dialog = {}
    for key in types_utterances:
        new_dialog[key] = []
        for utter in dialog.get(key, []):
            new_utter = {}
            for wanted_key in wanted_keys:
                if wanted_key in utter:
                    new_utter[wanted_key] = utter[wanted_key]
            new_dialog[key] += [new_utter]
    return new_dialog


def last_n_human_utt_dialog_formatter(dialog: Dict, last_n_utts: int, only_last_sentence: bool = False) -> List:
    """
    Args:
        dialog (Dict): full dialog state
        last_n_utts (int): how many last user utterances to take
        only_last_sentence (bool, optional): take only last sentence in each utterance. Defaults to False.
    """
    dialog = deepcopy(dialog)
    if len(dialog["human_utterances"]) <= last_n_utts and not if_lets_chat_about_topic(
            dialog["utterances"][0]["text"].lower()
    ):
        # in all cases when not particular topic, convert first phrase in the dialog to `hello!`
        if "sentseg" in dialog["human_utterances"][0]["annotations"]:
            dialog["human_utterances"][0]["annotations"]["sentseg"]["punct_sent"] = "hello!"
            dialog["human_utterances"][0]["annotations"]["sentseg"]["segments"] = ["hello"]
        else:
            dialog["human_utterances"][0]["text"] = "hello"

    human_utts = []
    detected_intents = []
    for utt in dialog["human_utterances"][-last_n_utts:]:
        if "sentseg" in utt["annotations"]:
            sentseg_ann = utt["annotations"]["sentseg"]
            if only_last_sentence:
                text = sentseg_ann["segments"][-1] if len(sentseg_ann["segments"]) > 0 else ""
            else:
                text = sentseg_ann["punct_sent"]
        else:
            text = utt["text"]
        human_utts += [text]
        detected_intents += [get_intents(utt, which="all")]
    return [{"sentences_batch": [human_utts], "intents": [detected_intents]}]


def stop_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: stop annotator, conv eval annotator
    hypotheses = dialog["utterances"][-1]["hypotheses"]
    utts = []
    for h in hypotheses:
        tmp_utts = [m["text"] for m in dialog["utterances"]]
        tmp_utts.append(h["text"])
        tmp_utts = " [SEP] ".join([j for j in tmp_utts])
        utts.append(tmp_utts)
    return [{"dialogs": utts}]


def dff_formatter(dialog: Dict, service_name: str, bot_last_turns=1, human_last_turns=1) -> List[Dict]:
    # DialoFlow Framework formatter
    state_name = f"{service_name}_state"
    human_utter_index = len(dialog["human_utterances"]) - 1

    human_attributes = dialog.get("human", {}).get("attributes", {})
    state = human_attributes.get(state_name, {})
    entities = human_attributes.get("entities", {})

    dialog = get_last_n_turns(dialog, bot_last_turns=bot_last_turns, human_last_turns=human_last_turns)
    dialog = replace_with_annotated_utterances(dialog, mode="punct_sent")

    # rm all execpt human_utterances, bot_utterances
    # we need only: text, annotations, active_skill
    new_dialog = clean_up_utterances_to_avoid_unwanted_keys(
        dialog, types_utterances=["human_utterances", "bot_utterances"]
    )

    return [
        {
            "human_utter_index_batch": [human_utter_index],
            "dialog_batch": [new_dialog],
            f"{state_name}_batch": [state],
            "entities_batch": [entities],
        }
    ]
