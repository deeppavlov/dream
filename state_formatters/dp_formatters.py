import logging
from copy import deepcopy
from typing import Dict, List

from common.universal_templates import if_lets_chat_about_topic
from common.utils import service_intents
import state_formatters.utils as utils

logger = logging.getLogger(__name__)


def alice_formatter_dialog(dialog: Dict) -> List:
    # Used by: alice
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=4)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    return utils.last_n_human_utt_dialog_formatter(dialog, last_n_utts=2, only_last_sentence=True)


def programy_formatter_dialog(dialog: Dict) -> List:
    # Used by: program_y, program_y_dangerous, program_y_wide
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=6)
    first_uttr_hi = False
    if len(dialog["utterances"]) == 1 and not if_lets_chat_about_topic(dialog["human_utterances"][-1]["text"]):
        first_uttr_hi = True

    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.last_n_human_utt_dialog_formatter(dialog, last_n_utts=5)[0]
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
    return [{"sentences_batch": [sentences]}]


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
    # Used by: cobot_qa_formatter
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
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [
        {
            "utterances_histories": [[utt["text"] for utt in dialog["utterances"]]],
            "personality": [dialog["bot"]["persona"]],
            "num_ongoing_utt": [utils.count_ongoing_skill_utterances(dialog["bot_utterances"], "convert_reddit")],
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
        return {"text": payload[0], "confidence": payload[1], "is_blacklisted": payload[2]}
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
            "speeches": [dialog["utterances"][-1].get("attributes", {}).get("speech", {})],
            "human_utterances": [dialog["human_utterances"][-3:]],
        }
    ]


def last_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    return [{"sentences": [dialog["utterances"][-1]["text"]]}]


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


def last_bot_utt_dialog(dialog: Dict) -> List[Dict]:
    return [{"sentences": [dialog["bot_utterances"][-1]["text"]]}]


def last_human_utt_nounphrases(dialog: Dict) -> List[Dict]:
    # Used by: comet_conceptnet_annotator
    return [{"nounphrases": [dialog["human_utterances"][-1]["annotations"].get("cobot_nounphrases", [])]}]


def hypotheses_list(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    return [{"sentences": hypots}]


def hypotheses_list_last_uttr(dialog: Dict) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    last_human_utterances = [dialog["human_utterances"][-1]["text"] for h in hypotheses]
    return [{"sentences": hypots, "last_human_utterances": last_human_utterances}]


def last_utt_and_history_dialog(dialog: Dict) -> List:
    # Used by: topicalchat retrieval skills
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    sent = dialog["human_utterances"][-1]["annotations"].get(
        "spelling_preprocessing", dialog["human_utterances"][-1]["text"]
    )
    return [{"sentences": [sent], "utterances_histories": [[utt["text"] for utt in dialog["utterances"]]]}]


def cobot_conv_eval_formatter_dialog(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog, total_last_turns=4)
    payload = utils.stop_formatter_dialog(dialog)
    # print(f"formatter {payload}", flush=True)
    return payload


def cobot_convers_evaluator_annotator_formatter(dialog: Dict) -> List[Dict]:
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    conv = dict()
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    conv["hypotheses"] = [h["text"] for h in hypotheses]
    conv["currentUtterance"] = dialog["utterances"][-1]["text"]
    # cobot recommends to take 2 last utt for conversation evaluation service
    conv["pastUtterances"] = [uttr["text"] for uttr in dialog["human_utterances"]][-3:-1]
    conv["pastResponses"] = [uttr["text"] for uttr in dialog["bot_utterances"]][-2:]
    return [conv]


def dp_classes_formatter_service(payload: List):
    # Used by: dp_toxic_formatter
    return payload[0]


def base_formatter_service(payload: List) -> List[Dict]:
    """
    Used by: dummy_skill_formatter, intent_responder_formatter, transfertransfo_formatter,
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


def full_history_dialog(dialog: Dict):
    """
    Used ONLY by: response selector and greeting_skill (turns on only for first 10 turns)
    """
    return [{"dialogs": [dialog]}]


def utt_sentrewrite_modified_last_dialog(dialog: Dict):
    # Used by: book_skill_formatter; misheard_asr_formatter, cobot_qa_formatter
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="modified_sents")
    return [{"dialogs": [dialog]}]


def utt_sentrewrite_modified_last_dialog_emotion_skill(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=25)
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
    if "sentseg" in dialog["utterances"][-1]["annotations"]:
        return [{"sentences": [dialog["utterances"][-1]["annotations"]["sentseg"]["segments"]]}]
    else:
        segments = [dialog["utterances"][-1]["text"]]
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
    entity_ids_batch, _, _ = dialog["human_utterances"][-1]["annotations"].get("entity_linking", [[], [], []])
    input_entity_ids = []
    input_entity_ids_list = []
    if entity_ids_batch:
        for entity_ids_list in entity_ids_batch:
            if entity_ids_list:
                input_entity_ids.append(entity_ids_list[0])
                input_entity_ids_list.append(entity_ids_list[:5])
    parser_info = ["find_top_triplets"]
    if not input_entity_ids_list:
        input_entity_ids_list = [[]]
    return [{"parser_info": parser_info, "query": [input_entity_ids_list]}]


def el_formatter_dialog(dialog: Dict):
    # Used by: entity_linking annotator
    ner_output = dialog["human_utterances"][-1]["annotations"].get("ner", [])
    nounphrases = dialog["human_utterances"][-1]["annotations"].get("cobot_nounphrases", [])
    entity_substr = []
    if ner_output:
        for entities in ner_output:
            for entity in entities:
                if entity and isinstance(entity, dict) and "text" in entity and entity["text"].lower() != "alexa":
                    entity_substr.append(entity["text"])

    if "sentseg" in dialog["human_utterances"][-1]["annotations"]:
        last_human_utterance_text = dialog["human_utterances"][-1]["annotations"]["sentseg"]["punct_sent"]
    else:
        last_human_utterance_text = dialog["human_utterances"][-1]["text"]
    if nounphrases:
        entity_substr += nounphrases
    entity_substr = list(set(entity_substr))

    return [{"entity_substr": [entity_substr], "template": [""], "context": [last_human_utterance_text]}]


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
    ner_output = annotations["ner"]
    entity_substr = [[entity["text"] for entity in entities] for entities in ner_output]
    nounphrases = annotations.get("cobot_nounphrases", [])
    entities = []
    for n, entities_list in enumerate(entity_substr):
        if entities_list:
            entities.append([entities_list[0]])
        elif nounphrases and len(nounphrases) > n:
            entities.append(nounphrases[n])
        else:
            entities.append([])
    if not entities:
        entities = [[] for _ in sentences]
    entities = entities[: len(sentences)]

    return [{"x_init": sentences, "entities": entities}]


def fact_retrieval_formatter_dialog(dialog: Dict):
    # Used by: odqa annotator
    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog_history = [" ".join([uttr["text"] for uttr in dialog["utterances"][-3:]])]

    last_human_utt = dialog["human_utterances"][-1]

    nounphrases = [last_human_utt["annotations"].get("cobot_nounphrases", [])]

    _, _, first_par_batch = \
        last_human_utt["annotations"].get("entity_linking", [[], [], []])

    return [
        {
            "human_sentences": [last_human_utt["text"]],
            "dialog_history": dialog_history,
            "entity_substr": nounphrases,
            "first_par": [first_par_batch],
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


def intent_responder_formatter_dialog(dialog: Dict):
    # Used by: intent_responder
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    intents = list(dialog["utterances"][-1]["annotations"]["intent_catcher"].keys())
    called_intents = {intent: False for intent in intents}
    for utt in dialog["human_utterances"][-5:-1]:
        called = [intent for intent, value in utt["annotations"].get("intent_catcher", {}).items() if value["detected"]]
        for intent in called:
            called_intents[intent] = True
    dialog["called_intents"] = called_intents
    dialog["utterances"] = dialog["utterances"][-(utils.LAST_N_TURNS * 2 + 1):]
    for utt in dialog["utterances"]:
        if "sentseg" in utt["annotations"]:
            utt["text"] = utt["annotations"]["sentseg"]["punct_sent"]
    return [{"dialogs": [dialog]}]


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

    dialog = utils.get_last_n_turns(dialog, bot_last_turns=1, human_last_turns=2)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="clean_sent")

    # rm all execpt human_utterances, bot_utterances
    # we need only: text, annotations, active_skill
    new_dialog = utils.clean_up_utterances_to_avoid_unwanted_keys(
        dialog, types_utterances=["human_utterances", "bot_utterances"]
    )

    new_dialog["human"] = {"attributes": attributes}

    return [{"human_utter_indexes": [human_utter_index], "dialogs": [new_dialog]}]


def dff_friendship_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_friendship_skill")


def dff_template_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_template")


def dff_celebrity_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_celebrity_skill")


def dff_music_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_music_skill")


def dff_animals_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_animals_skill")


def dff_sport_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_sport_skill")


def dff_travel_skill_formatter(dialog: Dict) -> List[Dict]:
    return utils.dff_formatter(dialog, "dff_travel_skill")


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


def dff_food_skill_formatter(dialog: Dict) -> List[Dict]:
    service_name = f"dff_food_skill"
    return utils.dff_formatter(dialog, service_name)


def game_cooperative_skill_formatter(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog["human"]["attributes"] = {
        "game_cooperative_skill": dialog["human"]["attributes"].get("game_cooperative_skill", {}),
        "used_links": dialog["human"]["attributes"].get("used_links", {}),
    }
    return [{"dialogs": [dialog]}]
