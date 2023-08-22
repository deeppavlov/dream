from typing import Dict, List, Union, Any
import logging
from copy import deepcopy
import re

from common.universal_templates import if_chat_about_particular_topic
from common.utils import get_intents, service_intents, get_entities
from common.grounding import BUT_PHRASE, REPEAT_PHRASE

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
    utterance_texts = [utterance["text"] for utterance in dialog["utterances"][-total_last_turns:]]
    for utterance_text in utterance_texts:
        if "#repeat" in utterance_text:  # Not to lose history on each repeat
            human_last_turns += 1
            bot_last_turns += 1
            total_last_turns += 2
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
    detected_interrupt = any(
        [interrupt_phrase in utt.get("text", "") for interrupt_phrase in [BUT_PHRASE, REPEAT_PHRASE]]
    )
    if is_asr or is_repeated or detected_interrupt:
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
            utt["orig_text"] = utt["text"]
            if "sentseg" in utt["annotations"]:
                utt["text"] = utt["annotations"]["sentseg"]["punct_sent"]
    elif mode == "segments":
        for utt in dialog["utterances"] + dialog["human_utterances"] + dialog["bot_utterances"]:
            utt["orig_text"] = utt["text"]
            if "sentseg" in utt["annotations"]:
                utt["text"] = deepcopy(utt["annotations"]["sentseg"]["segments"])
            elif isinstance(utt["text"], str):
                utt["text"] = [utt["text"]]
    elif mode == "modified_sents":
        for utt in dialog["utterances"] + dialog["human_utterances"]:
            utt["orig_text"] = utt["text"]
            if "sentrewrite" in utt["annotations"]:
                utt["text"] = utt["annotations"]["sentrewrite"]["modified_sents"][-1]
            elif "sentseg" in utt["annotations"]:
                utt["text"] = utt["annotations"]["sentseg"]["punct_sent"]
    elif mode == "clean_sent":
        for utt in dialog["utterances"] + dialog["human_utterances"] + dialog["bot_utterances"]:
            utt["orig_text"] = utt["text"]
            utt["text"] = clean_text(utt["text"])
    return dialog


def clean_up_utterances_to_avoid_unwanted_keys(
    dialog,
    wanted_keys=["text", "annotations", "active_skill", "user"],
    types_utterances=["human_utterances", "bot_utterances", "utterances"],
    used_annotations=None,
):
    # Attention! It removes all other keys from the dialog
    new_dialog = {}
    for key in types_utterances:
        new_dialog[key] = []
        for utter in dialog.get(key, []):
            new_utter = {}
            for wanted_key in wanted_keys:
                if wanted_key in utter:
                    if used_annotations and isinstance(used_annotations, list) and wanted_key == "annotations":
                        new_annotations = {}
                        for annotation_key in used_annotations:
                            if annotation_key in utter[wanted_key]:
                                new_annotations[annotation_key] = utter[wanted_key][annotation_key]
                        new_utter[wanted_key] = new_annotations
                    else:
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
    if len(dialog["human_utterances"]) <= last_n_utts and not if_chat_about_particular_topic(
        dialog["human_utterances"][0]
    ):
        # in all cases when not particular topic, convert first phrase in the dialog to `hello!`
        if "sentseg" in dialog["human_utterances"][0].get("annotations", {}):
            dialog["human_utterances"][0]["annotations"]["sentseg"]["punct_sent"] = "hello!"
            dialog["human_utterances"][0]["annotations"]["sentseg"]["segments"] = ["hello"]
        else:
            dialog["human_utterances"][0]["text"] = "hello"

    human_utts = []
    detected_intents = []
    for utt in dialog["human_utterances"][-last_n_utts:]:
        if "sentseg" in utt.get("annotations", {}):
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


def count_ongoing_skill_utterances(bot_utterances: List[Dict], skill: str) -> int:
    i = 0
    for utt in bot_utterances[::-1]:
        if utt["active_skill"] == skill:
            i += 1
        else:
            break
    return i


def dff_formatter(
    dialog: Dict,
    service_name: str,
    bot_last_turns=1,
    human_last_turns=1,
    used_annotations=None,
    types_utterances=None,
    wanted_keys=None,
) -> List[Dict]:
    types_utterances = ["human_utterances", "bot_utterances"] if types_utterances is None else types_utterances
    wanted_keys = ["text", "annotations", "active_skill", "user"] if wanted_keys is None else wanted_keys
    # DialoFlow Framework formatter
    state_name = f"{service_name}_state"
    human_utter_index = len(dialog["human_utterances"]) - 1

    human_attributes = dialog.get("human", {}).get("attributes", {})
    state = human_attributes.get(state_name, {})
    dff_shared_state = human_attributes.get("dff_shared_state", {"cross_states": {}, "cross_links": {}})
    used_links = human_attributes.get("used_links", {})
    age_group = human_attributes.get("age_group", "")
    disliked_skills = human_attributes.get("disliked_skills", {})
    entities = human_attributes.get("entities", {})
    prompts_goals = human_attributes.get("prompts_goals", {})

    previous_human_utter_index = state.get("previous_human_utter_index", -1)
    checking_unclarified_n_turns = human_utter_index - previous_human_utter_index
    if 1 < checking_unclarified_n_turns <= LAST_N_TURNS and previous_human_utter_index != -1:
        turns = list(
            zip(
                dialog["human_utterances"][-checking_unclarified_n_turns:],
                dialog["bot_utterances"][-checking_unclarified_n_turns:],
            )
        )
        unclarified_turns = [
            None
            for hu, bu in turns
            if is_human_uttr_repeat_request_or_misheard(hu) and is_bot_uttr_repeated_or_misheard(bu)
        ]
        clarification_request_flag = len(unclarified_turns) == 1
    else:
        clarification_request_flag = False

    dialog = get_last_n_turns(dialog)
    dialog = remove_clarification_turns_from_dialog(dialog)
    dialog = get_last_n_turns(dialog, bot_last_turns=bot_last_turns, human_last_turns=human_last_turns)
    dialog = replace_with_annotated_utterances(dialog, mode="punct_sent")

    # rm all execpt human_utterances, bot_utterances
    # we need only: text, annotations, active_skill
    new_dialog = clean_up_utterances_to_avoid_unwanted_keys(
        dialog, wanted_keys=wanted_keys, types_utterances=types_utterances, used_annotations=used_annotations
    )

    return [
        {
            "human_utter_index_batch": [human_utter_index],
            "dialog_batch": [new_dialog],
            f"{state_name}_batch": [state],
            "dff_shared_state_batch": [dff_shared_state],
            "entities_batch": [entities],
            "used_links_batch": [used_links],
            "age_group_batch": [age_group],
            "disliked_skills_batch": [disliked_skills],
            "prompts_goals_batch": [prompts_goals],
            "clarification_request_flag_batch": [clarification_request_flag],
            "dialog_id_batch": [dialog["dialog_id"]],
        }
    ]


def programy_post_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: program_y, program_y_dangerous, program_y_wide
    # Look at skills/program_y*
    dialog = get_last_n_turns(dialog, bot_last_turns=6)
    first_uttr_hi = False
    if len(dialog["human_utterances"]) == 1 and not if_chat_about_particular_topic(dialog["human_utterances"][-1]):
        first_uttr_hi = True

    dialog = remove_clarification_turns_from_dialog(dialog)
    dialog = last_n_human_utt_dialog_formatter(dialog, last_n_utts=5)[0]
    sentences = dialog["sentences_batch"][0]
    intents = dialog["intents"][0]

    # modify sentences with yes/no intents to yes/no phrase
    # todo: sent may contain multiple sentence, logic here could be improved
    prioritized_intents = service_intents - {"yes", "no"}
    for i, (sent, ints) in enumerate(zip(sentences, intents)):
        ints = set(ints)
        if "?" not in sent and len(ints & prioritized_intents) == 0:
            if "yes" in ints:
                sentences[i] = "yes."
            elif "no" in ints:
                sentences[i] = "no."
    if first_uttr_hi:
        sentences = ["hi."]
    return {"sentences_batch": [sentences]}


def preprocess_dialog(
    dialog: Dict,
    params: Dict = {"mode": "punct_sent", "bot_last_turns": None, "remove_clarification": False, "replace_utterances": False},
) -> Dict:
    dialog = get_last_n_turns(dialog, bot_last_turns=params.get("bot_last_turns"))
    if params.get("remove_clarification"):
        dialog = remove_clarification_turns_from_dialog(dialog)
    if params.get("replace_utterances"):
        dialog = replace_with_annotated_utterances(dialog, mode=params.get("mode", "punct_sent"))
    return dialog


def get_annotation(
    dialog: Dict,
    annotation_type: str,
    default_result: Any = None,
    last_n_utts: int = 1,
    utterance_type: str = "human_utterances",
) -> List[Dict]:
    return dialog[utterance_type][-last_n_utts]["annotations"].get(annotation_type, default_result)


def get_annotation_histories(dialog: Dict) -> List:
    return [[deepcopy(utt.get("annotations")) for utt in dialog["utterances"]]]


def get_human_utterance_history(dialog: Dict) -> List:
    history = []
    prev_human_utterance = None
    for utt in dialog["utterances"]:
        if utt["user"]["user_type"] == "human":
            prev_human_utterance = utt["annotations"].get("spelling_preprocessing", utt["text"])
        elif utt["user"]["user_type"] == "bot" and utt["active_skill"] == "eliza" and prev_human_utterance is not None:
            history.append(prev_human_utterance)
    return history


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


def get_triplets_entities(dialog):
    entity_substr_list, entity_tags_list = extract_entities(dialog["human_utterances"][-1])
    triplets = dialog["human_utterances"][-1]["annotations"].get("property_extraction", [{}])
    for triplet in triplets:
        object_entity_substr = triplet.get("object", "")
        if object_entity_substr and object_entity_substr not in entity_substr_list:
            entity_substr_list.append(object_entity_substr)
            entity_tags_list.append([["misc", 1.0]])


def get_x_init(dialog):
    annotations = dialog["human_utterances"][-1]["annotations"]
    if "sentseg" in annotations:
        if "segments" in annotations["sentseg"]:
            sentences = deepcopy(annotations["sentseg"]["segments"])
        else:
            sentences = [deepcopy(annotations["sentseg"]["punct_sent"])]
    else:
        sentences = [deepcopy(dialog["human_utterances"][-1]["text"])]
    return sentences


def get_utterances_attribute(dialog: Dict, params: Dict) -> List:
    if params.get("last_n_utts") > 0:
        dialog_slice = dialog[params["utterance_type"]][-params["last_n_utts"]]
    else:
        dialog_slice = dialog[params["utterance_type"]]

    if params.get("attribute") is None:
        return dialog_slice

    if params["utterance_type"] == "human_utterance" and params["attribute"] == "attributes":
        return [dialog_slice.get(params["attribute"], params["def_result"])]
    else:
        dialog_slice = dialog_slice.get(params["attribute"], params["def_result"])

    if params.get("sub_attribute") is None:
        return [utt.get(params["attribute"], params["def_result"]) for utt in dialog_slice]

    return [
        utt.get(params["attribute"], params["def_result"]).get(params["sub_attribute"], params["def_subresult"])
        for utt in dialog_slice
    ]


def get_ongoing_utterances(dialog):
    return [count_ongoing_skill_utterances(dialog["bot_utterances"], "convert_reddit")]


def get_entities_with_labels(dialog: Dict) -> Union[List[Dict[str, str]], List]:
    return get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=True)


def get_tokenized_sentences(dialog: Dict) -> List[List[str]]:
    tokens = get_utterances_attribute(
        dialog,
        params={
            "utterance_type": "human_utterance",
            "last_n_turns": 1,
            "attribute": "annotations",
            "def_result": "",
            "sub_attribute": "spacy_annotator",
            "def_subresult": [],
        },
    )
    tokens = [token["text"] for token in tokens]
    return [tokens] if len(tokens) else None


def get_sentences_with_history(dialog: Dict) -> List[str]:
    # get the two most recent bot and human utterances, and the last human utterance
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


def get_active_skills(dialog: Dict) -> List:
    active_skills = get_utterances_attribute(
        dialog, params={"utterance_type": "utterance", "attribute": "active_skill", "def_result": ""}
    )
    return [[skill for skill in active_skills if skill]]


def get_cobot_topics(dialog: Dict) -> List[List[str]]:
    return [
        [
            topic
            for utt in dialog["utterances"]
            for topic in utt.get("annotations", {}).get("cobot_topics", {}).get("text", [])
        ]
    ]


def get_contexts(dialog: Dict):
    hypots = [h["text"] for h in dialog["human_utterances"][-1]["hypotheses"]]
    contexts = len(hypots) * [dialog["human_utterances"][-1]["text"]]
    return contexts


def get_midas_preparation(dialog: Dict):
    midas_dist = get_intents(dialog["human_utterances"][-1], probs=True, which="midas")
    return [max(midas_dist, key=midas_dist.get)]


def get_fact_entities(dialog: Dict):
    last_human_utt = dialog["human_utterances"][-1]

    entity_info_list = last_human_utt["annotations"].get("entity_linking", [{}])
    entity_substr_list = []

    for entity_info in entity_info_list:
        if "entity_pages" in entity_info and entity_info["entity_pages"]:
            entity_substr_list.append(entity_info["entity_substr"])

    return entity_substr_list


def fetch_active_skills(dialog: Dict):
    all_prev_active_skills = [uttr.get("active_skill", "") for uttr in dialog["bot_utterances"]]
    return [skill_name for skill_name in all_prev_active_skills if skill_name]


def get_entity_info(dialog, param: str):
    necessary_info = []
    entity_info_list = dialog["human_utterances"][-1]["annotations"].get("entity_linking", [{}])
    for entity_info in entity_info_list:
        if "pages_titles" in entity_info and entity_info.get("pages_titles"):
            necessary_info.append(entity_info[param])
    return necessary_info


def get_dialog_history(dialog, last_n_utts: int = 2):
    return [" ".join([uttr["text"] for uttr in dialog["utterances"][-last_n_utts:]])]


def get_new_dialog(dialog):
    attributes = {"entities": dialog.get("human", {}).get("attributes", {}).get("entities", {})}

    # rm all execpt human_utterances, bot_utterances
    # we need only: text, annotations, active_skill
    new_dialog = clean_up_utterances_to_avoid_unwanted_keys(
        dialog, types_utterances=["human_utterances", "bot_utterances"]
    )

    new_dialog["human"] = {"attributes": attributes}

    return new_dialog


def get_sents(dialog: Dict):
    sents = [utt["text"] for utt in dialog["utterances"]]
    pointer = (len(sents) + 1) % 6 if (len(sents) + 1) % 6 != 0 else 6
    sents = sents[-(pointer + 5) :]
    return [sents]


def get_previous_summary(dialog: Dict):
    bot_attributes = dialog["bot_utterances"][-1]["user"]["attributes"] if len(dialog["bot_utterances"]) else {}
    previous_summary = bot_attributes["summarized_dialog"] if "summarized_dialog" in bot_attributes.keys() else []
    previous_summary = previous_summary if previous_summary else ""
    return [previous_summary]


def service_multiple_choices(dialog: Dict, service_name: str, params: Dict = None):
    if service_name == "convert":
        dialog_20 = get_last_n_turns(dialog, bot_last_turns=20)
        return [[utt["text"] for utt in dialog_20["utterances"]]]
    elif service_name == "sentrewrite" and params:
        utterances_histories = [utt["text"] for utt in dialog["utterances"][: -params.get("crop")]]
        return [[utterances_histories]]
    elif service_name in ("entity-detection", "property-extraction"):
        return [[uttr["text"] for uttr in dialog["utterances"][-params.get("crop") :]]]
    elif service_name == "seq2seq-persona-based":
        utterances_histories = [utt["text"] for utt in dialog["utterances"]]
        amount_utterances_history = 3
        utterances_histories = utterances_histories[-amount_utterances_history:]
        return [utterances_histories]
    else:
        return get_utterances_attribute(dialog, params)


def dream_formatter(
    dialog: Dict,
    result_keys: List,
    service_name: str = "",
    preprocess: bool = False,
    preprocess_params: Dict = None,
    additional_params: Dict = None,
) -> List:
    """
    Args:
        service_name: name of the service
        dialog: full dialog state
        result_keys: list of keys in result dialog
        preprocess: preprocess dialog
        preprocess_params: parameters for preprocessing
        additional_params: additional parameters for dialog processing

    Returns
        formatted dialog
    """
    if preprocess:
        dialog = preprocess_dialog(dialog, preprocess_params)

    keys_table = {
        (
            "last_utterance",
            "last_utterance_batch",
            "sentences",
            "speeches",
            "human_utterance",
            "utterances_histories",
            "utterances",
            "image_paths",
        ): service_multiple_choices,
        "human_utterance_history_batch": get_human_utterance_history,
        "personality": lambda dialog: [dialog["bot"]["persona"]]
        if service_name == "convert"
        else get_utterances_attribute,
        "annotation_histories": get_annotation_histories,
        "entities_with_labels": get_entities_with_labels,
        ("named_entities", "entity_info", "last_utterances"): get_annotation,
        "x_init": get_x_init,
        "sentences_with_history": get_sentences_with_history,
        "utterances_with_histories": get_utterances_with_histories,
        "cobot_topics": get_cobot_topics,
        "dialog_context": get_contexts,
        "last_midas_labels": get_midas_preparation,
        "entities": get_fact_entities,
        ("all_prev_active_skills", "active_skills"): fetch_active_skills,
        "nounphrases": get_entities,
        "dialog_history": get_dialog_history,
        "dialogs": clean_up_utterances_to_avoid_unwanted_keys,
        "new_dialog": get_new_dialog,
        "previous_summaries": get_previous_summary,
        "last_annotated_utterances": get_utterances_attribute,
        ("states_batch", "dialogs"): lambda dialog: get_sents if service_name == "summarization-annotator" else dialog,
    }

    lambda_keys_table = {
        "return_probas": 1,
        "human_utter_index": lambda dialog: len(dialog["utterances"] - 1),
        "num_ongoing_utt": lambda dialog: [count_ongoing_skill_utterances(dialog["bot_utterances"], "convert_reddit")],
        "human_sentences": lambda dialog: dialog["human_sentences"][-1]["text"],
        "hypotheses": lambda dialog: [h["text"] for h in dialog["human_utterances"][-1]["hypotheses"]],
        "dialog_contexts": lambda dialog: len([h["text"] for h in dialog["human_utterances"][-1]["hypotheses"]])
        * dialog["human_utterances"][-1]["text"],
        "contexts": lambda dialog: [uttr["text"] for uttr in dialog["utterances"][-4:]],
        "prompt_goals": lambda dialog: dialog["human"]["attributes"].get("prompts_goals", {}),
        "human_attributes": lambda dialog: dialog["human"]["attributes"],
    }

    formatted_dialog = dict()

    for result_key in result_keys:
        for key in keys_table.keys():
            if isinstance(key, tuple):
                if result_key in key:
                    if additional_params and service_name != "":
                        formatted_dialog[result_key] = keys_table[key](dialog, service_name, additional_params)
                    elif additional_params and service_name == "":
                        formatted_dialog[result_key] = keys_table[key](dialog, additional_params)
                    else:
                        formatted_dialog[result_key] = keys_table[key](dialog)
            else:
                if additional_params and service_name != "":
                    formatted_dialog[result_key] = keys_table[key](dialog, service_name, additional_params)
                elif additional_params:
                    formatted_dialog[result_key] = keys_table[key](dialog, service_name, additional_params)
                else:
                    formatted_dialog[result_key] = keys_table[key](dialog)

    for result_key in result_keys:
        if lambda_keys_table.get(result_key):
            formatted_dialog[result_key] = lambda_keys_table[result_key](dialog)

    if formatted_dialog.get("tokenized_sentences") is None:
        del formatted_dialog["tokenized_sentences"]

    return [formatted_dialog]
