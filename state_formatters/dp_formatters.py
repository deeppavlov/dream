import logging
from copy import deepcopy
from typing import Dict, List


from common.utils import get_entities, get_intents
import state_formatters.utils as utils

logger = logging.getLogger(__name__)


def base_skill_selector_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: base_skill_selector_formatter
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=5)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{"states_batch": [dialog]}]


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


def property_extraction_formatter_dialog(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog_history = [uttr["text"] for uttr in dialog["utterances"][-2:]]
    entities_with_labels = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=True)
    entity_info_list = dialog["human_utterances"][-1]["annotations"].get("entity_linking", [{}])
    named_entities = dialog["human_utterances"][-1]["annotations"].get("ner", [{}])
    return [
        {
            "utterances": [dialog_history],
            "entities_with_labels": [entities_with_labels],
            "named_entities": [named_entities],
            "entity_info": [entity_info_list],
        }
    ]


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


def last_bot_utt_dialog(dialog: Dict) -> List[Dict]:
    if len(dialog["bot_utterances"]):
        return [{"sentences": [dialog["bot_utterances"][-1]["text"]]}]
    else:
        return [{"sentences": [""]}]


def last_human_bot_annotated_utterance(dialog: Dict) -> List[Dict]:
    return [
        {
            "last_human_utterances": [dialog["human_utterances"][-1]],
            "bot_utterances": [dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}],
            "dialog_ids": [dialog.get("dialog_id", "unknown")],
        }
    ]


def hypotheses_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    return [{"sentences": hypots}]


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
    return [
        {
            "sentences": [sent],
            "utterances_histories": [[utt["text"] for utt in dialog["utterances"]]],
        }
    ]


def summarization_annotator_formatter(dialog: Dict):
    # Used by: summarization annotator
    sents = [utt["text"] for utt in dialog["utterances"]]
    pointer = (len(sents) + 1) % 6 if (len(sents) + 1) % 6 != 0 else 6
    sents = sents[-(pointer + 5) :]
    bot_attributes = dialog["bot_utterances"][-1]["user"]["attributes"] if len(dialog["bot_utterances"]) else {}
    previous_summary = bot_attributes["summarized_dialog"] if "summarized_dialog" in bot_attributes.keys() else []
    previous_summary = previous_summary if previous_summary else ""
    return [{"dialogs": [sents], "previous_summaries": [previous_summary]}]


def sentence_ranker_formatter(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    last_human_uttr = dialog["human_utterances"][-1]["text"]
    sentence_pairs = [[last_human_uttr, h["text"]] for h in dialog["human_utterances"][-1]["hypotheses"]]
    return [{"sentence_pairs": sentence_pairs}]


def simple_formatter_service(payload: List):
    logging.info(f"answer {payload}")
    return payload


def cropped_dialog(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=10)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{"dialogs": [dialog]}]


def full_history_dialog(dialog: Dict):
    # Used by: book_skill_formatter; misheard_asr_formatter, cobot_qa_formatter
    all_prev_active_skills = [uttr.get("active_skill", "") for uttr in dialog["bot_utterances"]]
    all_prev_active_skills = [skill_name for skill_name in all_prev_active_skills if skill_name]
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=20)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="modified_sents")
    return [{"dialogs": [dialog], "all_prev_active_skills": [all_prev_active_skills]}]


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
    if len(dialog["bot_utterances"]):
        if "sentseg" in dialog["bot_utterances"][-1]["annotations"]:
            return [{"last_utterances": [dialog["bot_utterances"][-1]["annotations"]["sentseg"]["segments"]]}]
        else:
            segments = [dialog["bot_utterances"][-1]["text"]]
            return [{"last_utterances": [segments]}]
    else:
        return [{"last_utterances": [[""]]}]


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


def prepare_el_input(dialog: Dict):
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
    context = [uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]

    return entity_substr_list, entity_tags_list, context


def el_formatter_dialog(dialog: Dict):
    # Used by: entity_linking annotator
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

    return [
        {
            "x_init": sentences,
            "entities": [entity_substr_list],
            "entity_tags": [entity_tags_list],
        }
    ]


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


def dff_image_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_image_skill")


def dff_prompted_skill_formatter(dialog, skill_name=None):
    return utils.dff_formatter(
        dialog,
        skill_name,
        bot_last_turns=5,
        types_utterances=["human_utterances", "bot_utterances", "utterances"],
        wanted_keys=["text", "annotations", "active_skill", "user", "attributes", "bot"],
    )


def context_formatter_dialog(dialog: Dict) -> List[Dict]:
    num_last_utterances = 4
    dialog = utils.get_last_n_turns(dialog, total_last_turns=num_last_utterances)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    contexts = [uttr["text"] for uttr in dialog["utterances"][-num_last_utterances:]]
    prompts_goals = dialog["human"]["attributes"].get("prompts_goals", {})
    return [
        {
            "contexts": [contexts],
            "prompts_goals": [prompts_goals],
            "last_human_utterances": [dialog["human_utterances"][-1]],
            "pipelines": [dialog.get("attributes", {}).get("pipeline", [])],
        }
    ]


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


def image_captioning_formatter(dialog: Dict) -> List[Dict]:
    # Used by: image_captioning
    return [{"image_paths": [dialog["human_utterances"][-1].get("attributes", {}).get("image")]}]


def robot_formatter(dialog: Dict) -> List[Dict]:
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


def cropped_dialog_skills_and_docs(dialog: Dict):
    all_prev_active_skills = [uttr.get("active_skill", "") for uttr in dialog["bot_utterances"]]
    all_prev_active_skills = [skill_name for skill_name in all_prev_active_skills if skill_name]
    all_prev_used_docs = [
        uttr.get("user", {}).get("attributes", {}).get("documents_in_use", []) for uttr in dialog["human_utterances"]
    ]
    all_prev_used_docs = [doc for doc in all_prev_used_docs if doc]
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [
        {
            "dialogs": [dialog],
            "all_prev_active_skills": [all_prev_active_skills],
            "all_prev_used_docs": [all_prev_used_docs],
        }
    ]
