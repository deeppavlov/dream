import logging
from copy import deepcopy
from typing import Dict, List, Any, Tuple, Optional, Union

from common.utils import get_entities, get_intents
import state_formatters.utils as utils

logger = logging.getLogger(__name__)


def preprocess_dialog(
        dialog: Dict,
        params: Dict = {
            "mode": "",
            "bot_last_turns": None,
            "remove_clarification": False,
            "replace_utterances": False
        }
) -> Dict:
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=params["bot_last_turns"])
    if params["remove_clarification"]:
        dialog = utils.remove_clarification_turns_from_dialog(dialog)
    if params["replace_utterances"]:
        dialog = utils.replace_with_annotated_utterances(dialog, mode=params["mode"])
    return dialog


def get_history(dialog):
    history = []
    prev_human_utterance = None
    for utt in dialog["utterances"]:
        if utt["user"]["user_type"] == "human":
            prev_human_utterance = utt["annotations"].get("spelling_preprocessing", utt["text"])
        elif utt["user"]["user_type"] == "bot" and utt["active_skill"] == "eliza" and prev_human_utterance is not None:
            history.append(prev_human_utterance)
    return history


def get_utterance_histories(dialog):
    return [[utt["text"] for utt in dialog["utterances"]]]


def get_annotation_histories(dialog):
    return [[deepcopy(utt.get("annotations")) for utt in dialog["utterances"]]]


def get_ongoing_utterances(dialog):
    return [utils.count_ongoing_skill_utterances(dialog["bot_utterances"], "convert_reddit")]


def get_human_attributes(dialog):
    return [dialog["human"]["attributes"]]


def get_text(dialog):
    return dialog["human_utterances"][-1]["annotations"].get(
        "spelling_preprocessing", dialog["human_utterances"][-1]["text"])


def get_speeches(dialog: Dict) -> Dict:
    return dialog["human_utterances"][-1].get("attributes", {}).get("speech", {})


def get_human_utterances(dialog: Dict) -> List[Dict]:
    return dialog["human_utterances"][-3:]


def get_dialog_history(dialog: Dict) -> List[str]:
    return [uttr["text"] for uttr in dialog["utterances"][-2:]]


def get_entities_with_labels(dialog: Dict) -> Any:  # replace Any with the actual return type of get_entities
    return get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=True)


def get_entity_info(dialog: Dict) -> List[Dict]:
    return dialog["human_utterances"][-1]["annotations"].get("entity_linking", [{}])


def get_named_entities(dialog: Dict) -> List[Dict]:
    return dialog["human_utterances"][-1]["annotations"].get("ner", [{}])


def get_tokenized_sentences(dialog: Dict) -> List[List[str]]:
    tokens = dialog["human_utterances"][-1]["annotations"].get("spacy_annotator", [])
    tokens = [token["text"] for token in tokens]
    return [tokens] if len(tokens) else None


def get_sentences_with_history(dialog: Dict) -> List[str]:
    last_human_utt = get_text(dialog)[0]
    if dialog["bot_utterances"]:
        # h sep b sep h sep b sep h
        prev_bot_utts = [k["text"] for k in dialog["bot_utterances"][-2:]]
        prev_human_utts = [
            utt["annotations"].get("spelling_preprocessing", utt["text"]) for utt in dialog["human_utterances"][-3:-1]
        ]
        prev_utts = []
        for human_utt, bot_utt in zip(prev_human_utts, prev_bot_utts):
            prev_utts.append(human_utt)
            prev_utts.append(bot_utt)
        sentence_w_history = " [SEP] ".join(prev_utts + [last_human_utt])
    else:
        sentence_w_history = last_human_utt
    return [sentence_w_history]


def get_utterance_batch(utterance: Union[str, Dict]) -> str:
    return " ".join(utterance["text"]) if isinstance(utterance["text"], list) else utterance["text"]


def get_utterances_with_histories(dialog: Dict) -> List[List[str]]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    dialog = preprocess_dialog(dialog, {"mode": "segments", "remove_clarification": True, "replace_utterances": True})
    utterances_histories_batch = []
    for hyp in hypotheses:
        utterances_histories = []
        for utt in dialog["utterances"]:
            utterances_histories = get_utterance_batch(utt)
        # hyp["text"] is a string. We need to pass here list of strings.
        utterances_histories.append(hyp["text"])
        utterances_histories_batch.append(utterances_histories)
    return utterances_histories_batch


def unified_formatter(
        dialog: Dict,
        result_keys: List,
        service_name: str = "",
        last_n_utts: int = None,
        preprocess: bool = False,
        preprocess_params: Dict = None
) -> List:
    """
    Parameters
    ----------
    service_name: name of the service
    dialog: full dialog state
    result_keys: list of keys in result dialog
    last_n_utts: how many last user utterances to take
    preprocess: preprocess dialog,
    preprocess_params: preprocess_params

    Returns
    -------
    formatted dialog
    """
    if preprocess:
        dialog = preprocess_dialog(dialog, preprocess_params)

    keys_table = {
        "speeches": get_speeches,
        "human_utterances": get_human_utterances,
        "last_utterance": get_text,
        "last_utternace_batch": get_text,
        "human_utterance_history_batch": get_history,
        "personality": lambda dialog: dialog["bot"]["persona"] if "convert" == "convert" else get_text(dialog),
        "states_batch": lambda dialog: dialog,
        "utterances_histories": get_utterance_histories,
        "annotation_histories": get_annotation_histories,
        "sentences": get_text,
        "contexts": get_utterance_histories,
        "utterances": get_dialog_history,
        "entities_with_labels": get_entities_with_labels,
        "named_entities": get_named_entities,
        "entity_info": get_entity_info,
        "sentences_with_history": get_sentences_with_history,
        "utterances_with_histories": get_utterances_with_histories
    }

    formatted_dialog = {key: keys_table[key](dialog) for key in result_keys}

    if formatted_dialog.get("tokenized_sentences") is None:
        del formatted_dialog["tokenized_sentences"]

    return [formatted_dialog]


def eliza_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: eliza_formatter
    return unified_formatter(
        service_name="eliza", dialog=dialog,
        result_keys=["last_utterance_batch", "human_utterance_history_batch"],
        preprocess=False
    )

def cobot_asr_formatter_service(payload: List):
    # Used by: cobot_qa, misheard_asr_formatter, personality_catcher_formatter
    hyps = []
    if len(payload) == 4:
        for resp, conf, ha, ba in zip(payload[0], payload[1], payload[2], payload[3]):
            if len(resp) > 0 and conf > 0.0:
                hyps.append(
                    {
                        "text": resp,
                        "confidence": conf,
                        "human_attributes": ha,
                        "bot_attributes": ba,
                    }
                )
        return hyps
    elif len(payload) == 3:
        return [
            {
                "text": payload[0],
                "confidence": payload[1],
                "personality": payload[2],
                "bot_attributes": {"persona": payload[2]},
            }
        ]


def base_skill_selector_formatter_dialog(dialog: Dict) -> List[Dict]:
    return unified_formatter(preprocess=True, preprocess_params={"bot_last_turns": 5, "mode": "punct_sent"},
                             dialog=dialog, result_keys=["states_batch"])


def convert_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: convert
    return unified_formatter(
        dialog, service_name="convert",
        result_keys=["utterances_histories", "personality", "num_ongoing_utt", "human_attributes"],
        preprocess=True, preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": None,
            "remove_clarification": False,
            "replace_utterances": False
        }
    )


def personality_catcher_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: personality_catcher_formatter
    return unified_formatter(dialog, result_keys=["personality"])


def sent_rewrite_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sent_rewrite_formatter
    return unified_formatter(
        dialog, result_keys=["utterances_histories", "annotation_histories"],
        preprocess=True, preprocess_params={"bot_last_turns": utils.LAST_N_TURNS}
    )


def sent_rewrite_formatter_w_o_last_dialog(dialog: Dict) -> List[Dict]:
    return unified_formatter(
        dialog, result_keys=["utterances_histories", "annotation_histories"],
        preprocess=True, preprocess_params={"bot_last_turns": utils.LAST_N_TURNS + 1}
    )


def cobot_formatter_dialog(dialog: Dict):
    # Used by: cobot_dialogact_formatter, cobot_classifiers_formatter
    return unified_formatter(
        dialog, result_keys=["utterances_histories", "annotation_histories"],
        preprocess=True, preprocess_params={"bot_last_turns": utils.LAST_N_TURNS}
    )


def base_response_selector_formatter_service(payload: List):
    # Used by: base_response_selector_formatter
    if len(payload) == 3:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2]}
    elif len(payload) == 5:
        return {
            "skill_name": payload[0],
            "text": payload[1],
            "confidence": payload[2],
            "human_attributes": payload[3],
            "bot_attributes": payload[4],
        }
    elif len(payload) == 6:
        return {
            "skill_name": payload[0],
            "text": payload[1],
            "confidence": payload[2],
            "human_attributes": payload[3],
            "bot_attributes": payload[4],
            "attributes": payload[5],
        }


def asr_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: asr_formatter
    return unified_formatter(
        dialog=dialog,
        result_keys=["speeches", "human_utterances"],
        preprocess=False,
        preprocess_params=None
    )


def last_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    return unified_formatter(dialog, result_keys=["sentences"])


def preproc_last_human_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return unified_formatter(dialog, result_keys=["speeches"], service_name="sentseg")


def entity_detection_formatter_dialog(dialog: Dict) -> List[Dict]:
    return unified_formatter(
        dialog, result_keys=["sentences"], preprocess=True,
        preprocess_params={"mode": "punct_sent", "remove_clarification": False, "replace_utterances": False}
    )


def property_extraction_formatter_dialog(dialog: Dict) -> List[Dict]:
    return unified_formatter(
        dialog=dialog,
        result_keys=["utterances", "entities_with_labels", "named_entities", "entity_info"],
        last_n_utts=2,
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent", "bot_last_turns": 1, "remove_clarification": False, "replace_utterances": True
        },
    )


def preproc_last_human_utt_dialog_w_hist(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return unified_formatter(
        dialog=dialog,
        result_keys=["sentences", "sentences_with_history"],
        service_name="preproc_last_human_utt_dialog_w_hist",
    )


def preproc_and_tokenized_last_human_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return unified_formatter(dialog=dialog, result_keys=["sentences", "tokenized_sentences"])


def last_bot_utt_dialog(dialog: Dict) -> List[Dict]:
    if len(dialog["bot_utterances"]):
        return [{"sentences": [dialog["bot_utterances"][-1]["text"]]}]
    else:
        return [{"sentences": [""]}]


def last_bot_annotated_utterance(dialog: Dict) -> List[Dict]:
    return [
        {
            "bot_utterances": [dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}],
            "dialog_ids": [dialog.get("dialog_id", "unknown")],
        }
    ]


def last_human_bot_annotated_utterance(dialog: Dict) -> List[Dict]:
    return [
        {
            "last_human_utterances": [dialog["human_utterances"][-1]],
            "bot_utterances": [dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}],
            "dialog_ids": [dialog.get("dialog_id", "unknown")],
        }
    ]


def last_human_utt_nounphrases(dialog: Dict) -> List[Dict]:
    # Used by: comet_conceptnet_annotator
    entities = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
    return [{"nounphrases": [entities]}]


def hypotheses_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    return [{"sentences": hypots}]


def hypotheses_list_last_uttr(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    last_human_utterances = [dialog["human_utterances"][-1]["text"] for h in hypotheses]
    return [{"sentences": hypots, "last_human_utterances": last_human_utterances}]


def hypothesis_histories_list(dialog: Dict):
    return unified_formatter(
        dialog=dialog,
        result_keys=["utterances_with_histories"],
        last_n_utts=1,
        preprocess=True,
        preprocess_params={
            "mode": "segments",
            "remove_clarification": True,
            "replace_utterances": True
        },
    )


def last_utt_and_history_dialog(dialog: Dict) -> List:
    # Used by: topicalchat retrieval skills
    return unified_formatter(
        dialog,
        result_keys=["sentences", "utterances_histories"],
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": None,
            "remove_clarification": False,
            "replace_utterances": False
        }
    )


def summarization_annotator_formatter(dialog: Dict):
    # Used by: summarization annotator
    sents = [utt["text"] for utt in dialog["utterances"]]
    pointer = (len(sents) + 1) % 6 if (len(sents) + 1) % 6 != 0 else 6
    sents = sents[-(pointer + 5) :]
    bot_attributes = dialog["bot_utterances"][-1]["user"]["attributes"] if len(dialog["bot_utterances"]) else {}
    previous_summary = bot_attributes["summarized_dialog"] if "summarized_dialog" in bot_attributes.keys() else []
    previous_summary = previous_summary if previous_summary else ""
    return [{"dialogs": [sents], "previous_summaries": [previous_summary]}]


def convers_evaluator_annotator_formatter(dialog: Dict) -> List[Dict]:
    dialog = preprocess_dialog(dialog, "", True, False)
    conv = dict()
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    conv["hypotheses"] = [h["text"] for h in hypotheses]
    conv["currentUtterance"] = dialog["human_utterances"][-1]["text"]
    # cobot recommends to take 2 last utt for conversation evaluation service
    conv["pastUtterances"] = [uttr["text"] for uttr in dialog["human_utterances"]][-3:-1]
    conv["pastResponses"] = [uttr["text"] for uttr in dialog["bot_utterances"]][-2:]
    return [conv]


def sentence_ranker_formatter(dialog: Dict) -> List[Dict]:
    dialog = preprocess_dialog(dialog, remove_clarification=True, replace_utterances=False)
    last_human_uttr = dialog["human_utterances"][-1]["text"]
    sentence_pairs = [[last_human_uttr, h["text"]] for h in dialog["human_utterances"][-1]["hypotheses"]]
    return [{"sentence_pairs": sentence_pairs}]


def base_formatter_service(payload: List) -> List[Dict]:
    """
    Used by: dummy_skill_formatter, transfertransfo_formatter,
    aiml_formatter, alice_formatter, tfidf_formatter
    """
    if len(payload[0]) > 0 and payload[1] > 0.0:
        return [{"text": payload[0], "confidence": payload[1]}]
    else:
        return []


def simple_formatter_service(payload: List):
    """
    Used by: punct_dialogs_formatter, intent_catcher_formatter, asr_formatter,
    sent_rewrite_formatter, sent_segm_formatter, base_skill_selector_formatter
    """
    logging.info(f"answer {payload}")
    return payload


def utt_sentseg_unified_dialog(dialog: Dict, replace_utterances: bool = True) -> List[Dict]:
    dialog = preprocess_dialog(dialog, "punct_sent", remove_clarification=True, replace_utterances=replace_utterances)
    return [{"dialogs": [dialog]}]


def utt_sentseg_punct_dialog(dialog: Dict):
    """
    Used by: skill_with_attributes_formatter; punct_dialogs_formatter,
    dummy_skill_formatter, base_response_selector_formatter
    """
    return utt_sentseg_unified_dialog(dialog, replace_utterances=True)


def utt_non_punct_dialog(dialog: Dict):
    """
    Used by: book_skill
    """
    return utt_sentseg_unified_dialog(dialog, replace_utterances=False)


def persona_bot_formatter(dialog: Dict):
    distill_dialog = preprocess_dialog(dialog, "punct_sent", remove_clarification=True, replace_utterances=True)
    last_uttr = distill_dialog["human_utterances"][-1]

    utterances_histories = [utt["text"] for utt in distill_dialog["utterances"]]
    amount_utterances_history = 3
    utterances_histories = utterances_histories[-amount_utterances_history:]

    return [
        {
            "utterances_histories": [utterances_histories],
            "last_annotated_utterances": [last_uttr],
        }
    ]


def full_dialog(dialog: Dict):
    return [{"dialogs": [dialog]}]


def fetch_active_skills(bot_utterances: List[Dict]):
    all_prev_active_skills = [uttr.get("active_skill", "") for uttr in bot_utterances]
    return [skill_name for skill_name in all_prev_active_skills if skill_name]


def sentrewrite_dialog_formatter(dialog: Dict, bot_last_turns: Any, mode: str, active_skills: bool) -> List[Dict]:
    if active_skills:
        all_prev_active_skills = fetch_active_skills(dialog["bot_utterances"])
        all_prev_active_skills = all_prev_active_skills[-15:]

    dialog = preprocess_dialog(dialog, mode, bot_last_turns, remove_clarification=True, replace_utterances=True)

    if active_skills:
        return [{"dialogs": [dialog], "all_prev_active_skills": [all_prev_active_skills]}]
    else:
        return [{"dialogs": [dialog]}]


def full_history_dialog(dialog: Dict):
    return sentrewrite_dialog_formatter(dialog, bot_last_turns=10, mode="punct_sent", active_skills=True)


def utt_sentrewrite_modified_last_dialog(dialog: Dict):
    return sentrewrite_dialog_formatter(dialog, bot_last_turns=None, mode="modified_sents", active_skills=True)


def utt_sentrewrite_modified_last_dialog_emotion_skill(dialog: Dict):
    return sentrewrite_dialog_formatter(dialog, bot_last_turns=2, mode="modified_sents", active_skills=False)


def base_skill_formatter(payload: Dict):
    return [{"text": payload[0], "confidence": payload[1]}]


def skill_with_attributes_formatter_service(payload: List):
    """
    Formatter should use `"state_manager_method": "add_hypothesis"` in config!!!
    Because it returns list of hypothesis even if the payload is returned for one sample!
    Args:
        payload: if one sample, list of the following structure:
            (text, confidence, ^human_attributes, ^bot_attributes, attributes) [by ^ marked optional elements]
                if several hypothesis, list of lists of the above structure
    Returns:
        list of dictionaries of the following structure:
            {"text": text, "confidence": confidence_value,
             ^"human_attributes": {}, ^"bot_attributes": {},
             **attributes},
             by ^ marked optional elements
    """
    # Used by: book_skill_formatter, skill_with_attributes_formatter, news_skill, meta_script_skill, dummy_skill
    # deal with text & confidences
    if isinstance(payload[0], list) and isinstance(payload[1], list):
        # several hypotheses from this skill
        result = []
        for hyp in zip(*payload):
            if len(hyp[0]) > 0 and hyp[1] > 0.0:
                full_hyp = {"text": hyp[0], "confidence": hyp[1]}
                if len(payload) >= 4:
                    # have human and bot attributes in hyps
                    full_hyp["human_attributes"] = hyp[2]
                    full_hyp["bot_attributes"] = hyp[3]
                if len(payload) == 3 or len(payload) == 5:
                    # have also attributes in hyps
                    assert isinstance(hyp[-1], dict), "Attribute is a dictionary"
                    for key in hyp[-1]:
                        full_hyp[key] = hyp[-1][key]
                result += [full_hyp]
    else:
        # only one hypotheses from this skill
        if len(payload[0]) > 0 and payload[1] > 0.0:
            result = [{"text": payload[0], "confidence": payload[1]}]
            if len(payload) >= 4:
                # have human and bot attributes in hyps
                result[0]["human_attributes"] = payload[2]
                result[0]["bot_attributes"] = payload[3]
            if len(payload) == 3 or len(payload) == 5:
                # have also attributes in hyps
                assert isinstance(payload[-1], dict), "Attribute is a dictionary"
                for key in payload[-1]:
                    result[0][key] = payload[-1][key]
        else:
            result = []

    return result


def extract_segments_or_text(utterance: Dict):
    if "sentseg" in utterance["annotations"]:
        return utterance["annotations"]["sentseg"]["segments"]
    else:
        return [utterance["text"]]


def last_utt_sentseg_segments_dialog(dialog: Dict):
    # Used by: intent_catcher_formatter
    segments = extract_segments_or_text(dialog["human_utterances"][-1])
    return [{"sentences": [segments]}]


def ner_formatter_dialog(dialog: Dict):
    # Used by: ner_formatter
    segments = extract_segments_or_text(dialog["human_utterances"][-1])
    return [{"last_utterances": [segments]}]


def ner_formatter_last_bot_dialog(dialog: Dict):
    if len(dialog["bot_utterances"]):
        segments = extract_segments_or_text(dialog["bot_utterances"][-1])
    else:
        segments = [""]
    return [{"last_utterances": [segments]}]


def wp_formatter_dialog(dialog: Dict):
    # Used by: wiki_parser annotator
    entity_info_list = dialog["human_utterances"][-1]["annotations"].get("entity_linking", [{}])
    utt_index = len(dialog["human_utterances"])
    input_entity_info_list = []
    if entity_info_list:
        for entity_info in entity_info_list:
            if (
                    entity_info
                    and "entity_substr" in entity_info
                    and "entity_ids" in entity_info
                    and "tokens_match_conf" in entity_info
            ):
                input_entity_info_list.append(
                    {
                        "entity_substr": entity_info["entity_substr"],
                        "entity_ids": entity_info["entity_ids"][:5],
                        "confidences": entity_info["confidences"][:5],
                        "tokens_match_conf": entity_info["tokens_match_conf"][:5],
                    }
                )
    parser_info = ["find_top_triplets"]
    if not input_entity_info_list:
        input_entity_info_list = [{}]
    return [
        {
            "parser_info": parser_info,
            "query": [input_entity_info_list],
            "utt_num": utt_index,
        }
    ]


def extract_entities(utterance):
    entities_with_labels = get_entities(utterance, only_named=False, with_labels=True)
    entity_substr_list, entity_tags_list = [], []
    for entity in entities_with_labels:
        if entity and isinstance(entity, dict) and "text" in entity and entity["text"].lower() != "alexa":
            entity_substr_list.append(entity["text"])
            if "finegrained_label" in entity:
                finegrained_labels = [[label.lower(), conf] for label, conf in entity["finegrained_label"]]
                entity_tags_list.append(finegrained_labels)
            elif "label" in entity:
                entity_tags_list.append([[entity["label"].lower(), 1.0]])
            else:
                entity_tags_list.append([["misc", 1.0]])
    return entity_substr_list, entity_tags_list


def unified_el_kbqa_formatter_dialog(dialog: Dict, formatter_type: str) -> List[Dict]:
    if formatter_type == "el":
        num_last_utterances = 2
        entity_substr_list, entity_tags_list = extract_entities(dialog["human_utterances"][-1])
        triplets = dialog["human_utterances"][-1]["annotations"].get("property_extraction", [{}])
        for triplet in triplets:
            object_entity_substr = triplet.get("object", "")
            if object_entity_substr and object_entity_substr not in entity_substr_list:
                entity_substr_list.append(object_entity_substr)
                entity_tags_list.append([["misc", 1.0]])
        dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
        dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
        context = [[uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]]
        return [{"entity_substr": [entity_substr_list], "entity_tags": [entity_tags_list], "context": context}]

    elif formatter_type == "kbqa":
        annotations = dialog["human_utterances"][-1]["annotations"]
        if "sentseg" in annotations:
            if "segments" in annotations["sentseg"]:
                sentences = deepcopy(annotations["sentseg"]["segments"])
            else:
                sentences = [deepcopy(annotations["sentseg"]["punct_sent"])]
        else:
            sentences = [deepcopy(dialog["human_utterances"][-1]["text"])]
        entity_substr_list, entity_tags_list = extract_entities(dialog["human_utterances"][-1])
        return [{"x_init": sentences, "entities": [entity_substr_list], "entity_tags": [entity_tags_list]}]


def el_formatter_dialog(dialog: Dict):
    entity_substr_list, entity_tags_list, context = prepare_el_input(dialog)
    return [
        {
            "entity_substr": [entity_substr_list],
            "entity_tags": [entity_tags_list],
            "context": [context],
        }
    ]


def custom_el_formatter_dialog(dialog: Dict):
    # Used by: entity_linking annotator
    entity_substr_list, entity_tags_list, context = prepare_el_input(dialog)
    property_extraction = dialog["human_utterances"][-1]["annotations"].get("property_extraction", {})
    user_id = str(dialog["human_utterances"][-1].get("user", {}).get("id", ""))
    return [
        {
            "user_id": [user_id],
            "entity_substr": [entity_substr_list],
            "entity_tags": [entity_tags_list],
            "context": [context],
            "property_extraction": [property_extraction],
        }
    ]



def kbqa_formatter_dialog(dialog: Dict):
    return unified_el_kbqa_formatter_dialog(dialog, formatter_type="kbqa")


def fact_random_formatter_dialog(dialog: Dict):
    # Used by: fact-random annotator
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    last_human_utt = dialog["human_utterances"][-1]

    entity_info_list = last_human_utt["annotations"].get("entity_linking", [{}])
    entity_substr_list = []

    for entity_info in entity_info_list:
        if "entity_pages" in entity_info and entity_info["entity_pages"]:
            entity_substr_list.append(entity_info["entity_substr"])

    return [{"text": last_human_utt["text"], "entities": entity_substr_list}]


def fact_retrieval_formatter_dialog(dialog: Dict):
    # Used by: odqa annotator
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog_history = [" ".join([uttr["text"] for uttr in dialog["utterances"][-3:]])]

    last_human_utt = dialog["human_utterances"][-1]
    nounphrases = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)

    entity_info_list = last_human_utt["annotations"].get("entity_linking", [{}])
    entity_pages_list = []
    entity_ids_list = []
    entity_substr_list = []
    entity_pages_titles_list = []
    for entity_info in entity_info_list:
        if "pages_titles" in entity_info and entity_info["pages_titles"]:
            entity_pages_list.append(entity_info["first_paragraphs"])
            entity_ids_list.append(entity_info["entity_ids"])
            entity_substr_list.append(entity_info["entity_substr"])
            entity_pages_titles_list.append(entity_info["pages_titles"])
    return [
        {
            "human_sentences": [last_human_utt["text"]],
            "dialog_history": dialog_history,
            "nounphrases": [nounphrases],
            "entity_substr": [entity_substr_list],
            "entity_pages": [entity_pages_list],
            "entity_ids": [entity_ids_list],
            "entity_pages_titles": [entity_pages_titles_list],
        }
    ]


def fact_retrieval_rus_formatter_dialog(dialog: Dict):
    # Used by: odqa annotator
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog_history = [" ".join([uttr["text"] for uttr in dialog["utterances"][-2:]])]
    last_human_utt = dialog["human_utterances"][-1]

    entity_info_list = last_human_utt["annotations"].get("entity_linking", [{}])
    entity_substr_list, entity_tags_list, entity_pages_list = [], [], []
    for entity_info in entity_info_list:
        if "entity_pages" in entity_info and entity_info["entity_pages"]:
            entity_substr_list.append(entity_info["entity_substr"])
            entity_tags_list.append(entity_info["entity_tags"])
            entity_pages_list.append(entity_info["entity_pages"])
    return [
        {
            "dialog_history": [dialog_history],
            "entity_substr": [entity_substr_list],
            "entity_tags": [entity_tags_list],
            "entity_pages": [entity_pages_list],
        }
    ]


def entity_storer_formatter(dialog: Dict) -> List[Dict]:
    human_utter_index = len(dialog["human_utterances"]) - 1
    attributes = {"entities": dialog.get("human", {}).get("attributes", {}).get("entities", {})}

    dialog = utils.get_last_n_turns(dialog, bot_last_turns=5, human_last_turns=2)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")

    # rm all execpt human_utterances, bot_utterances
    # we need only: text, annotations, active_skill
    new_dialog = utils.clean_up_utterances_to_avoid_unwanted_keys(
        dialog, types_utterances=["human_utterances", "bot_utterances"]
    )

    new_dialog["human"] = {"attributes": attributes}

    return [{"human_utter_indexes": [human_utter_index], "dialogs": [new_dialog]}]


def dff_friendship_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_friendship_skill")


def dff_funfact_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_funfact_skill")


def dff_celebrity_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_celebrity_skill")


def dff_music_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_music_skill")


def dff_animals_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_animals_skill")


def dff_gaming_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_gaming_skill")


def dff_sport_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_sport_skill")


def dff_travel_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_travel_skill")


def dff_science_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_science_skill")


def dff_gossip_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_gossip_skill")


def dff_movie_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_movie_skill")


def dff_art_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_art_skill")


def dff_grounding_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_grounding_skill")


def dff_coronavirus_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_coronavirus_skill")


def dff_short_story_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_short_story_skill", human_last_turns=3)


def dff_generative_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_generative_skill")


def dff_template_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_template_skill")


def dff_intent_responder_skill_formatter(dialog: Dict) -> List[Dict]:
    intents = list(dialog["human_utterances"][-1]["annotations"].get("intent_catcher", {}).keys())
    called_intents = {intent: False for intent in intents}
    for utt in dialog["human_utterances"][-5:-1]:
        called = [intent for intent, value in utt["annotations"].get("intent_catcher", {}).items() if value["detected"]]
        for intent in called:
            called_intents[intent] = True

    batches = utils.dff_formatter(dialog, "dff_intent_responder_skill")
    batches[-1]["dialog_batch"][-1]["called_intents"] = called_intents
    batches[-1]["dialog_batch"][-1]["dialog_id"] = dialog.get("dialog_id", "unknown")
    return batches


def dff_program_y_wide_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_program_y_wide_skill")


def dff_program_y_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_program_y_skill")


def dff_food_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_food_skill")


def dff_bot_persona_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_bot_persona_skill")


def dff_book_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_book_skill")


def dff_book_sfc_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_book_sfc_skill")


def dff_weather_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_weather_skill")


def dff_wiki_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(
        dialog,
        "dff_wiki_skill",
        used_annotations=[
            "cobot_entities",
            "spacy_nounphrases",
            "entity_linking",
            "factoid_classification",
            "wiki_parser",
            "cobot_topics",
            "news_api_annotator",
        ],
    )


def dff_program_y_dangerous_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_program_y_dangerous_skill")


def dff_image_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_image_skill")


def dff_prompted_skill_formatter(dialog, skill_name=None):
    return utils.dff_formatter(
        dialog,
        skill_name,
        bot_last_turns=5,
        types_utterances=["human_utterances", "bot_utterances", "utterances"],
        wanted_keys=["text", "annotations", "active_skill", "user", "attributes"],
    )


def dff_universal_prompted_skill_formatter(dialog, skill_name=None):
    return utils.dff_formatter(
        dialog,
        "dff_universal_prompted_skill",
        bot_last_turns=5,
        types_utterances=["human_utterances", "bot_utterances", "utterances"],
        wanted_keys=["text", "annotations", "active_skill", "user", "attributes"],
    )


def get_utterance_info(utterance: Dict) -> Dict:
    sentseg = utterance.get("annotations", {}).get("sentseg", {})
    speech_function = utterance.get("annotations", {}).get("speech_function_classifier", [""])[-1]

    return {
        "phrase": sentseg.get("segments", [utterance["text"]]),
        "prev_speech_function": speech_function
    }


def get_previous_info(dialog: Dict, role: str, index: int) -> Dict:
    if role == 'human' and len(dialog[role + '_utterances']) > 1:
        return get_utterance_info(dialog[role + '_utterances'][index])
    elif role == 'bot' and dialog[role + '_utterances']:
        return get_utterance_info(dialog[role + '_utterances'][index])
    else:
        return {
            "prev_phrase": None,
            "prev_speech_function": None
        }


def game_cooperative_skill_formatter(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog["human"]["attributes"] = {
        "game_cooperative_skill": dialog["human"]["attributes"].get("game_cooperative_skill", {}),
        "used_links": dialog["human"]["attributes"].get("used_links", {}),
    }
    return [{"dialogs": [dialog]}]


def speech_function_formatter(dialog: Dict):
    human_sentseg = dialog["human_utterances"][-1].get("annotations", {}).get("sentseg", {})
    resp = {"phrase": human_sentseg.get("segments", [dialog["human_utterances"][-1]["text"]])}
    try:
        bot_sentseg = dialog["bot_utterances"][-1].get("annotations", {}).get("sentseg", {})
        resp["prev_phrase"] = bot_sentseg.get("segments", [dialog["bot_utterances"][-1]["text"]])[-1]
        bot_function = dialog["bot_utterances"][-1].get("annotations", {}).get("speech_function_classifier", [""])[-1]
        resp["prev_speech_function"] = bot_function
    except IndexError:
        resp["prev_phrase"] = None
        resp["prev_speech_function"] = None
    return [resp]


def speech_function_formatter(dialog: Dict) -> List[Dict]:
    resp = get_utterance_info(dialog['human_utterances'][-1])
    resp.update(get_previous_info(dialog, 'bot', -1))
    return [resp]


def speech_function_bot_formatter(dialog: Dict) -> List[Dict]:
    resp = get_utterance_info(dialog['bot_utterances'][-1])
    resp.update(get_previous_info(dialog, 'human', -2))
    return [resp]


def get_hypotheses_info(dialog: Dict) -> List[Dict]:
    return dialog["human_utterances"][-1]["hypotheses"]


def get_annotation_value(hypothesis: Dict, key: str) -> Any:
    return hypothesis["annotations"].get(key, [""])


def speech_function_annotation(dialog: Dict) -> List[Dict]:
    utterance_info = get_utterance_info(dialog['human_utterances'][-1])
    hypotheses = get_hypotheses_info(dialog)

    return [
        {
            "prev_phrase": utterance_info['phrase'][-1],
            "prev_speech_function": utterance_info['prev_speech_function'],
            "phrase": h["text"],
        }
        for h in hypotheses
    ]


def speech_function_predictor_formatter(dialog: Dict):
    return [get_annotation_value(dialog["human_utterances"][-1], "speech_function_classifier")]


def speech_function_hypotheses_predictor_formatter(dialog: Dict):
    hypotheses = get_hypotheses_info(dialog)
    return [get_annotation_value(h, "speech_function_classifier") for h in hypotheses]


def hypothesis_scorer_formatter(dialog: Dict) -> List[Dict]:
    hypotheses = get_hypotheses_info(dialog)

    result_hypotheses = [
        {
            "text": hyp["text"],
            "confidence": hyp.get("confidence", 0),
            "convers_evaluator_annotator": get_annotation_value(hyp, "convers_evaluator_annotator"),
        }
        for hyp in hypotheses
    ]

    contexts = len(hypotheses) * [[uttr["text"] for uttr in dialog["utterances"]]]

    return [{"contexts": contexts, "hypotheses": result_hypotheses}]


def topic_recommendation_formatter(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    active_skills, topics = [], []
    for utt in dialog["utterances"]:
        active_skills.append(utt.get("active_skill", ""))
        topics += utt.get("annotations", {}).get("cobot_topics", {}).get("text", [])
    active_skills = [skill for skill in active_skills if skill]
    return [{"active_skills": [active_skills], "cobot_topics": [topics]}]


def midas_predictor_formatter(dialog: Dict):
    last_uttr = dialog["human_utterances"][-1]
    midas_dist = get_intents(last_uttr, probs=True, which="midas")
    return [{"last_midas_labels": [max(midas_dist, key=midas_dist.get)], "return_probas": 1}]


def hypotheses_with_context_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]

    contexts = len(hypots) * [dialog["human_utterances"][-1]["text"]]

    return [{"dialog_contexts": contexts, "hypotheses": hypots}]


def context_formatter_dialog(dialog: Dict) -> List[Dict]:
<<<<<<< HEAD
    num_last_utterances = 4
    dialog = utils.get_last_n_turns(dialog, total_last_turns=num_last_utterances)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    contexts = [uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]
    prompts_goals = dialog["human"]["attributes"].get("prompts_goals", {})
    return [{"contexts": [contexts], "prompts_goals": [prompts_goals]}]


def prompts_goals_collector_formatter(dialog: Dict) -> List[Dict]:
    prompts_goals = {}
    if len(dialog["human_utterances"]) > 1:
        hypotheses = dialog["human_utterances"][-2].get("hypotheses", [])
        for prompts_goals_dict in [hyp.get("prompts_goals", None) for hyp in hypotheses]:
            if prompts_goals_dict:
                prompts_goals.update(deepcopy(prompts_goals_dict))
    return [
        {
            "prompts_goals": [prompts_goals],
            "human_attributes": [dialog["human"]["attributes"]],
        }
    ]
=======
    return unified_formatter(
        dialog, result_keys=["contexts"],
        preprocess=True, preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": 4,
            "remove_clarification": False,
            "replace_utterances": False
        }
    )
>>>>>>> 1125d5d23 (Add unified formatter)


def image_captioning_formatter(dialog: Dict) -> List[Dict]:
    # Used by: image_captioning
    return [{"image_paths": [dialog["human_utterances"][-1].get("attributes", {}).get("image")]}]


def external_integration_skill_formatter(dialog: Dict) -> List[Dict]:
    last_sentences = [dialog["human_utterances"][-1]["text"]]
    dialog_ids = [dialog.get("dialog_id", "unknown")]
    user_ids = [dialog["human_utterances"][-1]["user"]["id"]]
    return [{"sentences": last_sentences, "dialog_ids": dialog_ids, "user_ids": user_ids}]


def robot_formatter(dialog: Dict) -> Dict:
    """This formatter currently provides the JSON as is, without modifying it.
    Either edit it later or choose one of the existing formatters"""
    detected = get_intents(dialog["human_utterances"][-1], probs=True, which="intent_catcher")
    return [{"detected": detected}]


def dff_command_selector_skill_formatter(dialog: Dict) -> List[Dict]:
    intents = list(dialog["human_utterances"][-1]["annotations"].get("intent_catcher", {}).keys())
    called_intents = {intent: False for intent in intents}
    for utt in dialog["human_utterances"][-5:-1]:
        called = [intent for intent, value in utt["annotations"].get("intent_catcher", {}).items() if value["detected"]]
        for intent in called:
            called_intents[intent] = True

    batches = utils.dff_formatter(dialog, "dff_command_selector_skill")
    batches[-1]["dialog_batch"][-1]["called_intents"] = called_intents
    batches[-1]["dialog_batch"][-1]["dialog_id"] = dialog.get("dialog_id", "unknown")
    return batches
