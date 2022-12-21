import logging
from copy import deepcopy
from typing import Dict, List

from common.utils import get_entities, get_intents
import state_formatters.utils as utils

logger = logging.getLogger(__name__)


def alice_formatter_dialog(dialog: Dict) -> List:
    # Used by: alice
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=4)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    return utils.last_n_human_utt_dialog_formatter(dialog, last_n_utts=2, only_last_sentence=True)


def eliza_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: eliza_formatter
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    history = []
    prev_human_utterance = None
    for utt in dialog["utterances"]:
        if utt["user"]["user_type"] == "human":
            prev_human_utterance = utt["annotations"].get("spelling_preprocessing", utt["text"])
        elif utt["user"]["user_type"] == "bot" and utt["active_skill"] == "eliza" and prev_human_utterance is not None:
            history.append(prev_human_utterance)
    last_utterance = dialog["human_utterances"][-1]["annotations"].get(
        "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
    )
    return [
        {
            "last_utterance_batch": [last_utterance],
            "human_utterance_history_batch": [history],
        }
    ]


def cobot_qa_formatter_service(payload: List):
    # Used by: cobot_qa
    hyps = []
    for resp, conf in zip(payload[0], payload[1]):
        if len(resp) > 0 and conf > 0.0:
            hyps.append({"text": resp, "confidence": conf})
    return hyps


def misheard_asr_formatter_service(payload: List):
    # Used by: misheard_asr_formatter
    hyps = []
    for resp, conf, ha, ba in zip(payload[0], payload[1], payload[2], payload[3]):
        if len(resp) > 0 and conf > 0:
            hyps.append({"text": resp, "confidence": conf, "human_attributes": ha, "bot_attributes": ba})
    return hyps


def base_skill_selector_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: base_skill_selector_formatter
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=5)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{"states_batch": [dialog]}]


def convert_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: convert
    dialog_20 = utils.get_last_n_turns(dialog, bot_last_turns=20)
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [
        {
            "utterances_histories": [[utt["text"] for utt in dialog_20["utterances"]]],
            "personality": [dialog["bot"]["persona"]],
            "num_ongoing_utt": [utils.count_ongoing_skill_utterances(dialog["bot_utterances"], "convert_reddit")],
            "human_attributes": [dialog["human"]["attributes"]],
        }
    ]


def personality_catcher_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: personality_catcher_formatter
    return [
        {
            "personality": [
                dialog["human_utterances"][-1]["annotations"].get(
                    "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
                )
            ]
        }
    ]


def telegram_selector_formatter_in(dialog: Dict):
    return [dialog["human"]["attributes"]["active_skill"]]


def personality_catcher_formatter_service(payload: List):
    # Used by: personality_catcher_formatter
    return [
        {
            "text": payload[0],
            "confidence": payload[1],
            "personality": payload[2],
            "bot_attributes": {"persona": payload[2]},
        }
    ]


def cobot_classifiers_formatter_service(payload: List):
    # Used by: cobot_classifiers_formatter, sentiment_formatter
    if len(payload) == 3:
        return {"text": payload[0], "confidence": payload[1], "is_badlisted": payload[2]}
    elif len(payload) == 2:
        return {"text": payload[0], "confidence": payload[1]}
    elif len(payload) == 1:
        return {"text": payload[0]}
    elif len(payload) == 0:
        return {"text": []}


def cobot_dialogact_formatter_service(payload: List):
    # Used by: cobot_dialogact_formatter
    return {"intents": payload[0], "topics": payload[1]}


def cobot_formatter_dialog(dialog: Dict):
    # Used by: cobot_dialogact_formatter, cobot_classifiers_formatter
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="segments")
    utterances_histories = []
    for utt in dialog["utterances"]:
        utterances_histories.append(utt["text"])
    return [{"utterances_histories": [utterances_histories]}]


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


def sent_rewrite_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sent_rewrite_formatter
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="segments")
    utterances_histories = []
    annotation_histories = []
    for utt in dialog["utterances"]:
        annotation_histories.append(deepcopy(utt["annotations"]))
        utterances_histories.append(utt["text"])
    return [{"utterances_histories": [utterances_histories], "annotation_histories": [annotation_histories]}]


def sent_rewrite_formatter_w_o_last_dialog(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog, utils.LAST_N_TURNS + 1)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="segments")
    utterances_histories = []
    annotation_histories = []
    for utt in dialog["utterances"][:-1]:
        annotation_histories.append(deepcopy(utt["annotations"]))
        utterances_histories.append(utt["text"])
    return [{"utterances_histories": [utterances_histories], "annotation_histories": [annotation_histories]}]


def asr_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: asr_formatter
    return [
        {
            "speeches": [dialog["human_utterances"][-1].get("attributes", {}).get("speech", {})],
            "human_utterances": [dialog["human_utterances"][-3:]],
        }
    ]


def last_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    return [{"sentences": [dialog["human_utterances"][-1]["text"]]}]


def preproc_last_human_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return [
        {
            "sentences": [
                dialog["human_utterances"][-1]["annotations"].get(
                    "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
                )
            ]
        }
    ]


def entity_detection_formatter_dialog(dialog: Dict) -> List[Dict]:
    num_last_utterances = 2
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    context = [[uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]]
    return [{"sentences": context}]


def preproc_last_human_utt_dialog_w_hist(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    last_human_utt = dialog["human_utterances"][-1]["annotations"].get(
        "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
    )
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
    return [{"sentences": [last_human_utt], "sentences_with_history": [sentence_w_history]}]


def preproc_last_human_utt_and_nounphrases_dialog(dialog: Dict) -> List[Dict]:
    # Used by: cobot entities
    return [
        {
            "sentences": [
                dialog["human_utterances"][-1]["annotations"].get(
                    "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
                )
            ],
            "nounphrases": [dialog["human_utterances"][-1]["annotations"].get("spacy_nounphrases", [])],
        }
    ]


def preproc_and_tokenized_last_human_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    tokens = dialog["human_utterances"][-1]["annotations"].get("spacy_annotator", [])
    tokens = [token["text"] for token in tokens]
    result = [
        {
            "sentences": [
                dialog["human_utterances"][-1]["annotations"].get(
                    "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
                )
            ]
        }
    ]

    if len(tokens):
        result[0]["tokenized_sentences"] = [tokens]

    return result


def last_bot_utt_dialog(dialog: Dict) -> List[Dict]:
    if len(dialog["bot_utterances"]):
        return [{"sentences": [dialog["bot_utterances"][-1]["text"]]}]
    else:
        return [{"sentences": [""]}]


def last_bot_annotated_utterance(dialog: Dict) -> List[Dict]:
    if len(dialog["bot_utterances"]):
        return [{"bot_utterances": [dialog["bot_utterances"][-1]], "dialog_ids": [dialog.get("dialog_id", "unknown")]}]
    else:
        return [{"bot_utterances": [{}], "dialog_ids": [dialog.get("dialog_id", "unknown")]}]


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


def hypotheses_segmented_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [[h["text"]] for h in hypotheses]
    return [{"sentences": hypots}]


def tokenized_hypotheses_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    tokens = [h.get("annotations", {}).get("spacy_annotator", []) for h in hypotheses]
    tokens = [[token["text"] for token in h] for h in tokens]
    hypots = [h["text"] for h in hypotheses]
    if len(tokens):
        result = [{"sentences": hypots, "tokenized_sentences": tokens}]
    else:
        result = [{"sentences": hypots}]
    return result


def ner_hypotheses_segmented_list(dialog: Dict):
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [[h["text"]] for h in hypotheses]
    return [{"last_utterances": hypots}]


def hypothesis_histories_list(dialog: Dict):
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="segments")
    utterances_histories_batch = []
    for hyp in hypotheses:
        utterances_histories = []
        for utt in dialog["utterances"]:
            utt_text = utt["text"]
            if isinstance(utt_text, list):
                utt_text = " ".join(utt_text)
            utterances_histories.append(utt_text)
        # hyp["text"] is a string. We need to pass here list of strings.
        utterances_histories.append(hyp["text"])
        utterances_histories_batch.append(utterances_histories)

    return [{"utterances_with_histories": utterances_histories_batch}]


def last_utt_and_history_dialog(dialog: Dict) -> List:
    # Used by: topicalchat retrieval skills
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    sent = dialog["human_utterances"][-1]["annotations"].get(
        "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
    )
    return [{"sentences": [sent], "utterances_histories": [[utt["text"] for utt in dialog["utterances"]]]}]


def convers_evaluator_annotator_formatter(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    conv = dict()
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    conv["hypotheses"] = [h["text"] for h in hypotheses]
    conv["currentUtterance"] = dialog["human_utterances"][-1]["text"]
    # cobot recommends to take 2 last utt for conversation evaluation service
    conv["pastUtterances"] = [uttr["text"] for uttr in dialog["human_utterances"]][-3:-1]
    conv["pastResponses"] = [uttr["text"] for uttr in dialog["bot_utterances"]][-2:]
    return [conv]


def sentence_ranker_formatter(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    last_human_uttr = dialog["human_utterances"][-1]["text"]
    sentence_pairs = [[last_human_uttr, h["text"]] for h in dialog["human_utterances"][-1]["hypotheses"]]
    return [{"sentence_pairs": sentence_pairs}]


def dp_classes_formatter_service(payload: List):
    # Used by: dp_toxic_formatter
    return payload[0]


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


def simple_batch_formatter_service(payload: List):
    for i in range(len(payload["batch"])):
        if len(payload["batch"][i]) == 3:
            payload["batch"][i] = {
                "text": payload["batch"][i][0],
                "confidence": payload["batch"][i][1],
                "is_badlisted": payload["batch"][i][2],
            }
        elif len(payload["batch"][i]) == 2:
            payload["batch"][i] = {"text": payload["batch"][i][0], "confidence": payload["batch"][i][1]}
        elif len(payload["batch"][i]) == 1:
            payload["batch"][i] = {"text": payload["batch"][i][0]}
        elif len(payload["batch"][i]) == 0:
            payload["batch"][i] = {"text": []}
    return payload


def cobot_dialogact_batch_formatter_service(payload: List):
    for i in range(len(payload["batch"])):
        payload["batch"][i] = {"intents": payload["batch"][i][0], "topics": payload["batch"][i][1]}

    return payload


def utt_sentseg_punct_dialog(dialog: Dict):
    """
    Used by: skill_with_attributes_formatter; punct_dialogs_formatter,
    dummy_skill_formatter, base_response_selector_formatter
    """
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{"dialogs": [dialog]}]


def utt_non_punct_dialog(dialog: Dict):
    """
    Used by: book_skill
    """
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    return [{"dialogs": [dialog]}]


def persona_bot_formatter(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    distill_dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    last_uttr = distill_dialog["human_utterances"][-1]

    utterances_histories = [utt["text"] for utt in distill_dialog["utterances"]]
    amount_utterances_history = 3
    utterances_histories = utterances_histories[-amount_utterances_history:]

    return [{"utterances_histories": [utterances_histories], "last_annotated_utterances": [last_uttr]}]


def full_history_dialog(dialog: Dict):
    """
    Used ONLY by: response selector
    """
    all_prev_active_skills = [uttr.get("active_skill", "") for uttr in dialog["bot_utterances"]]
    all_prev_active_skills = [skill_name for skill_name in all_prev_active_skills if skill_name][-15:]
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=10)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{"dialogs": [dialog], "all_prev_active_skills": [all_prev_active_skills]}]


def utt_sentrewrite_modified_last_dialog(dialog: Dict):
    # Used by: book_skill_formatter; misheard_asr_formatter, cobot_qa_formatter
    all_prev_active_skills = [uttr.get("active_skill", "") for uttr in dialog["bot_utterances"]]
    all_prev_active_skills = [skill_name for skill_name in all_prev_active_skills if skill_name]
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="modified_sents")
    return [{"dialogs": [dialog], "all_prev_active_skills": [all_prev_active_skills]}]


def utt_sentrewrite_modified_last_dialog_emotion_skill(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=2)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="modified_sents")
    return [{"dialogs": [dialog]}]


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


def last_utt_sentseg_segments_dialog(dialog: Dict):
    # Used by: intent_catcher_formatter
    if "sentseg" in dialog["human_utterances"][-1]["annotations"]:
        return [{"sentences": [dialog["human_utterances"][-1]["annotations"]["sentseg"]["segments"]]}]
    else:
        segments = [dialog["human_utterances"][-1]["text"]]
        return [{"sentences": [segments]}]


def ner_formatter_dialog(dialog: Dict):
    # Used by: ner_formatter
    if "sentseg" in dialog["human_utterances"][-1]["annotations"]:
        return [{"last_utterances": [dialog["human_utterances"][-1]["annotations"]["sentseg"]["segments"]]}]
    else:
        segments = [dialog["human_utterances"][-1]["text"]]
        return [{"last_utterances": [segments]}]


def ner_formatter_last_bot_dialog(dialog: Dict):
    if "sentseg" in dialog["bot_utterances"][-1]["annotations"]:
        return [{"last_utterances": [dialog["bot_utterances"][-1]["annotations"]["sentseg"]["segments"]]}]
    else:
        segments = [dialog["bot_utterances"][-1]["text"]]
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
    return [{"parser_info": parser_info, "query": [input_entity_info_list], "utt_num": utt_index}]


def el_formatter_dialog(dialog: Dict):
    # Used by: entity_linking annotator
    num_last_utterances = 2
    entities_with_labels = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=True)
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
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    context = [[uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]]

    return [{"entity_substr": [entity_substr_list], "entity_tags": [entity_tags_list], "context": context}]


def kbqa_formatter_dialog(dialog: Dict):
    # Used by: kbqa annotator
    annotations = dialog["human_utterances"][-1]["annotations"]
    if "sentseg" in annotations:
        if "segments" in annotations["sentseg"]:
            sentences = deepcopy(annotations["sentseg"]["segments"])
        else:
            sentences = [deepcopy(annotations["sentseg"]["punct_sent"])]
    else:
        sentences = [deepcopy(dialog["human_utterances"][-1]["text"])]
    entities_with_labels = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=True)
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

    return [{"x_init": sentences, "entities": [entity_substr_list], "entity_tags": [entity_tags_list]}]


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


def short_story_formatter_dialog(dialog: Dict):
    # Used by: short_story_skill
    return [
        {
            "intents": dialog["human_utterances"][-1]["annotations"].get("intent_catcher", {}),
            "human_sentence": dialog["human_utterances"][-1]["annotations"].get(
                "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
            ),
            "state": dialog["bot"]["attributes"].get("short_story_skill_attributes", {}),
        }
    ]


def attitude_formatter_service(payload: List):
    # Used by: attitude_formatter
    payload = payload[0]
    if len(payload) == 2:
        return {"text": payload[0], "confidence": payload[1]}
    elif len(payload) == 1:
        return {"text": payload[0]}
    elif len(payload) == 0:
        return {"text": []}


def dialog_breakdown_formatter(dialog: Dict) -> List[Dict]:
    # Used by: dialog_breakdown
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=2)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    context = " ".join([uttr["text"] for uttr in dialog["utterances"][-4:-1]])
    return [{"context": [context], "curr_utterance": [dialog["human_utterances"][-1]["text"]]}]


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


def hypotheses_list_for_dialog_breakdown(dialog: Dict) -> List[Dict]:
    # Used by: dialog_breakdown
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=2)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    context = " ".join([uttr["text"] for uttr in dialog["utterances"][-3:]])
    hyps = {"context": [], "curr_utterance": []}
    for hyp in dialog["human_utterances"][-1]["hypotheses"]:
        hyps["context"].append(context)
        hyps["curr_utterance"].append(hyp["text"])
    return [hyps]


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


def speech_function_bot_formatter(dialog: Dict):
    bot_sentseg = dialog["bot_utterances"][-1].get("annotations", {}).get("sentseg", {})
    resp = {"phrase": bot_sentseg.get("segments", [dialog["bot_utterances"][-1]["text"]])}
    if len(dialog["human_utterances"]) > 1:
        human_sentseg = dialog["human_utterances"][-2].get("annotations", {}).get("sentseg", {})
        resp["prev_phrase"] = human_sentseg.get("segments", [dialog["human_utterances"][-2]["text"]])[-1]
        human_function = (
            dialog["human_utterances"][-2].get("annotations", {}).get("speech_function_classifier", [""])[-1]
        )
        resp["prev_speech_function"] = human_function
    else:
        resp["prev_phrase"] = None
        resp["prev_speech_function"] = None
    return [resp]


def speech_function_annotation(dialog: Dict):
    human_sentseg = dialog["human_utterances"][-1].get("annotations", {}).get("sentseg", {})
    prev_phrase = human_sentseg.get("segments", [dialog["human_utterances"][-1]["text"]])[-1]
    human_function = dialog["human_utterances"][-1].get("annotations", {}).get("speech_function_classifier", [""])[-1]
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    resp = [
        {"prev_phrase": prev_phrase, "prev_speech_function": human_function, "phrase": h["text"]} for h in hypotheses
    ]
    return [resp]


def speech_function_predictor_formatter(dialog: Dict):
    return [dialog["human_utterances"][-1]["annotations"].get("speech_function_classifier", [""])]


def speech_function_hypotheses_predictor_formatter(dialog: Dict):
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    ans = [h["annotations"].get("speech_function_classifier", [""]) for h in hypotheses]
    return ans


def hypothesis_scorer_formatter(dialog: Dict) -> List[Dict]:
    hypotheses = []
    for hyp in dialog["human_utterances"][-1]["hypotheses"]:
        hypotheses.append(
            {
                "text": hyp["text"],
                "confidence": hyp.get("confidence", 0),
                "convers_evaluator_annotator": hyp.get("annotations", {}).get("convers_evaluator_annotator", {}),
            }
        )

    contexts = len(hypotheses) * [[uttr["text"] for uttr in dialog["utterances"]]]

    return [{"contexts": contexts, "hypotheses": hypotheses}]


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
    midas_dist = dialog["human_utterances"][-1].get("annotations", {}).get("midas_classification", [{}])[-1]

    return [{"last_midas_labels": [max(midas_dist, key=midas_dist.get)], "return_probas": 1}]


def hypotheses_with_context_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]

    contexts = len(hypots) * [dialog["human_utterances"][-1]["text"]]

    return [{"dialog_contexts": contexts, "hypotheses": hypots}]


def context_formatter_dialog(dialog: Dict) -> List[Dict]:
    num_last_utterances = 4
    dialog = utils.get_last_n_turns(dialog, total_last_turns=num_last_utterances)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    contexts = [[uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]]
    return [{"contexts": contexts}]


def robot_formatter(dialog: Dict) -> Dict:
    """This formatter currently provides the JSON as is, without modifying it.
    Either edit it later or choose one of the existing formatters"""
    detected = get_intents(dialog["human_utterances"][-1], probs=True, which="intent_catcher")
    return [{"detected": detected}]
