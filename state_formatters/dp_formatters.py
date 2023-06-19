import logging
from typing import Dict, List, Any

from common.utils import get_entities
import state_formatters.utils as utils

logger = logging.getLogger(__name__)


def utt_sentseg_punct_dialog(dialog: Dict):
    """
    Used by: skill_with_attributes_formatter; punct_dialogs_formatter,
    dummy_skill_formatter, base_response_selector_formatter
    """
    return utils.dream_formatter(
        dialog,
        result_keys=["dialog"],
        preprocess=True,
        preprocess_params={"mode": "punct_sent", "remove_clarification": True, "replace_utterances": True},
    )


def utt_non_punct_dialog(dialog: Dict):
    """
    Used by: book_skill
    """
    return utils.dream_formatter(
        dialog,
        result_keys=["dialog"],
        preprocess=True,
        preprocess_params={"mode": "punct_sent", "remove_clarification": True, "replace_utterances": False},
    )


def eliza_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: eliza_formatter
    return utils.dream_formatter(
        service_name="eliza",
        dialog=dialog,
        result_keys=["last_utterance_batch", "human_utterance_history_batch"],
        preprocess=False,
    )


def base_skill_selector_formatter_dialog(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(
        dialog,
        result_keys=["states_batch"],
        preprocess=True,
        preprocess_params={"bot_last_turns": 5, "mode": "punct_sent"},
    )


def convert_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: convert
    return utils.dream_formatter(
        dialog,
        service_name="convert",
        result_keys=["utterances_histories", "personality", "num_ongoing_utt", "human_attributes"],
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": None,
            "remove_clarification": False,
            "replace_utterances": False,
        },
    )


def personality_catcher_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: personality_catcher_formatter
    return utils.dream_formatter(dialog, result_keys=["personality"])


def sent_rewrite_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sent_rewrite_formatter
    return utils.dream_formatter(
        dialog,
        result_keys=["utterances_histories", "annotation_histories"],
        preprocess=True,
        preprocess_params={"bot_last_turns": utils.LAST_N_TURNS},
    )


def sent_rewrite_formatter_w_o_last_dialog(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(
        dialog,
        result_keys=["utterances_histories", "annotation_histories"],
        preprocess=True,
        preprocess_params={"bot_last_turns": utils.LAST_N_TURNS + 1},
    )


def cobot_formatter_dialog(dialog: Dict):
    # Used by: cobot_dialogact_formatter, cobot_classifiers_formatter
    return utils.dream_formatter(
        dialog,
        result_keys=["utterances_histories", "annotation_histories"],
        preprocess=True,
        preprocess_params={"bot_last_turns": utils.LAST_N_TURNS},
    )


def asr_formatter_dialog(dialog: Dict) -> List[Dict]:
    # Used by: asr_formatter
    return utils.dream_formatter(dialog=dialog, result_keys=["speeches", "human_utterances"])


def last_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    return utils.dream_formatter(dialog, result_keys=["sentences"])


def preproc_last_human_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return utils.dream_formatter(dialog, result_keys=["speeches"], service_name="sentseg")


def entity_detection_formatter_dialog(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(
        dialog,
        result_keys=["sentences"],
        preprocess=True,
        preprocess_params={"mode": "punct_sent", "remove_clarification": False, "replace_utterances": False},
    )


def property_extraction_formatter_dialog(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(
        dialog=dialog,
        result_keys=["utterances", "entities_with_labels", "named_entities", "entity_info"],
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": 1,
            "remove_clarification": False,
            "replace_utterances": True,
        },
    )


def preproc_last_human_utt_dialog_w_hist(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return utils.dream_formatter(
        dialog=dialog,
        result_keys=["sentences", "sentences_with_history"],
        service_name="preproc_last_human_utt_dialog_w_hist",
    )


def preproc_and_tokenized_last_human_utt_dialog(dialog: Dict) -> List[Dict]:
    # Used by: sentseg over human uttrs
    return utils.dream_formatter(dialog=dialog, result_keys=["sentences", "tokenized_sentences"])


def last_human_bot_annotated_utterance(dialog: Dict) -> List[Dict]:
    return [
        {
            "last_human_utterances": [dialog["human_utterances"][-1]],
            "bot_utterances": [dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}],
            "dialog_ids": [dialog.get("dialog_id", "unknown")],
        }
    ]


def generate_hypotheses_list(dialog: Dict, include_last_utterance: bool = False) -> List[Dict]:
    hypotheses = dialog["human_utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]

    if include_last_utterance:
        last_human_utterances = [dialog["human_utterances"][-1]["text"] for h in hypotheses]
        # return [{"sentences": hypots, "last_human_utterances": last_human_utterances}]
        return utils.dream_formatter(dialog, result_keys=["sentences", "last_human_utterances"])
    return utils.dream_formatter(dialog, result_keys=["sentences"])


def hypothesis_histories_list(dialog: Dict):
    return utils.dream_formatter(
        dialog=dialog,
        result_keys=["utterances_with_histories"],
        preprocess=True,
        preprocess_params={
            "mode": "segments",
            "remove_clarification": True,
            "replace_utterances": True,
        },
    )


def last_utt_and_history_dialog(dialog: Dict) -> List:
    # Used by: topicalchat retrieval skills
    return utils.dream_formatter(
        dialog,
        result_keys=["sentences", "utterances_histories"],
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": None,
            "remove_clarification": False,
            "replace_utterances": False,
        },
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
    return utils.dream_formatter(
        dialog,
        result_keys=["hypotheses", "currentUtterance", "pastUtter", "pastResponses"],
        preprocess=True,
        preprocess_params={"remove_clarification": True},
    )


def persona_bot_formatter(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        result_keys=["utterances_histories", "last_annotated_utterances"],
        preprocess=True,
        preprocess_params={"mode": "punct_sent", "remove_clarification": True, "replace_utterances": True},
    )


def cropped_dialog(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        result_keys=["dialogs"],
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": None,
            "remove_clarification": True,
            "replace_utterances": True,
        },
    )


def full_dialog(dialog: Dict):
    return utils.dream_formatter(dialog, result_keys=["dialogs"])


def full_history_dialog(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        result_keys=["dialogs", "all_prev_active_skills"],
        preprocess=True,
        preprocess_params={
            "mode": "modified_sents",
            "bot_last_turns": 10,
            "remove_clarification": True,
            "replace_utterances": True,
        },
    )


def utt_sentrewrite_modified_last_dialog(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        result_keys=["dialogs", "all_prev_active_skills"],
        preprocess=True,
        preprocess_params={
            "mode": "modified_sents",
            "remove_clarification": True,
            "replace_utterances": True,
        },
    )


def utt_sentrewrite_modified_last_dialog_emotion_skill(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        result_keys=["dialogs", "all_prev_active_skills"],
        preprocess=True,
        preprocess_params={
            "mode": "modified_sents",
            "bot_last_turns": 2,
            "remove_clarification": True,
            "replace_utterances": True,
        },
    )


def el_formatter_dialog(dialog: Dict):
    return utils.dream_formatter(dialog, result_keys=["entity_substr", "entity_tags"])


def kbqa_formatter_dialog(dialog: Dict):
    return utils.dream_formatter(dialog, result_keys=["x_init", "entities", "entity_tags"])


def topic_recommendation_formatter(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        result_keys=["active_skills", "cobot_topics"],
        preprocess=True,
        preprocess_params={"remove_clarification": True},
    )


def hypotheses_with_context_list(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(dialog, result_keys=["dialog_contexts", "hypotheses"])


def context_formatter_dialog(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(
        dialog,
        result_keys=["contexts"],
        preprocess=True,
        preprocess_params={
            "mode": "punct_sent",
            "bot_last_turns": 4,
            "remove_clarification": False,
            "replace_utterances": False,
        },
    )


def midas_predictor_formatter(dialog: Dict):
    return utils.dream_formatter(dialog, result_keys=["last_midas_labels", "return_probas"])


def fact_random_formatter_dialog(dialog: Dict):
    # Used by: fact-random annotator
    return utils.dream_formatter(
        dialog,
        result_keys=["text", "entities"],
        preprocess=True,
        preprocess_params={"bot_last_turns": 1, "mode": "punct_sent"},
    )


def fact_retrieval_formatter_dialog(dialog: Dict):
    # Used by: odqa annotator
    return utils.dream_formatter(
        dialog,
        result_keys=[
            "human_sentences",
            "dialog_history",
            "nounphrases",
            "entity_substr",
            "entity_pages",
            "entity_ids",
            "entity_pages_titles",
        ],
        preprocess=True,
        preprocess_params={"bot_last_turns": 1, "mode": "punct_sent"},
        additional_params={"params": ["first_paragraphs", "entity_ids", "entity_substr", "pages_titles"]},
    )


def fact_retrieval_rus_formatter_dialog(dialog: Dict):
    # Used by: odqa annotator
    return utils.dream_formatter(
        dialog,
        result_keys=["dialog_history", "entity_substr", "entity_tags", "entity_pages"],
        preprocess=True,
        preprocess_params={"bot_last_turns": 1, "mode": "punct_sent"},
        additional_params={"params": ["entity_substr", "entity_tags", "entity_pages"]},
    )


def entity_storer_formatter(dialog: Dict) -> List[Dict]:
    return utils.dream_formatter(
        dialog,
        result_keys=["human_utter_index", "dialogs"],
        preprocess=True,
        preprocess_params={"bot_last_turns": 5, "human_last_turns": 2, "mode": "punct_sent"},
    )


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


def dff_universal_prompted_skill_formatter(dialog):
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

    return {"phrase": sentseg.get("segments", [utterance["text"]]), "prev_speech_function": speech_function}


def get_previous_info(dialog: Dict, role: str, index: int) -> Dict:
    if role == "human" and len(dialog[role + "_utterances"]) > 1:
        return get_utterance_info(dialog[role + "_utterances"][index])
    elif role == "bot" and dialog[role + "_utterances"]:
        return get_utterance_info(dialog[role + "_utterances"][index])
    else:
        return {"prev_phrase": None, "prev_speech_function": None}


def game_cooperative_skill_formatter(dialog: Dict):
    dialog = utils.get_last_n_turns(dialog)
    dialog = utils.remove_clarification_turns_from_dialog(dialog)
    dialog = utils.replace_with_annotated_utterances(dialog, mode="punct_sent")
    dialog["human"]["attributes"] = {
        "game_cooperative_skill": dialog["human"]["attributes"].get("game_cooperative_skill", {}),
        "used_links": dialog["human"]["attributes"].get("used_links", {}),
    }
    return [{"dialogs": [dialog]}]


def speech_function_formatter(dialog: Dict) -> List[Dict]:
    resp = get_utterance_info(dialog["human_utterances"][-1])
    resp.update(get_previous_info(dialog, "bot", -1))
    return [resp]


def speech_function_bot_formatter(dialog: Dict) -> List[Dict]:
    resp = get_utterance_info(dialog["bot_utterances"][-1])
    resp.update(get_previous_info(dialog, "human", -2))
    return [resp]


def get_hypotheses_info(dialog: Dict) -> List[Dict]:
    return dialog["human_utterances"][-1]["hypotheses"]


def get_annotation_value(hypothesis: Dict, key: str) -> Any:
    return hypothesis["annotations"].get(key, [""])


def speech_function_annotation(dialog: Dict) -> List[Dict]:
    utterance_info = get_utterance_info(dialog["human_utterances"][-1])
    hypotheses = get_hypotheses_info(dialog)

    return [
        {
            "prev_phrase": utterance_info["phrase"][-1],
            "prev_speech_function": utterance_info["prev_speech_function"],
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


def last_bot_utt_dialog(dialog: Dict) -> List[Dict]:
    if len(dialog["bot_utterances"]):
        return [{"sentences": [dialog["bot_utterances"][-1]["text"]]}]
    else:
        return [{"sentences": [""]}]


def last_human_utt_nounphrases(dialog: Dict) -> List[Dict]:
    # Used by: comet_conceptnet_annotator
    entities = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)
    return [{"nounphrases": [entities]}]


def sentence_ranker_formatter(dialog: Dict) -> List[Dict]:
    dialog = utils.preprocess_dialog(
        dialog, params={"mode": "", "remove_clarifications": True, "replace_utterances": False}
    )
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


def base_skill_formatter(payload: Dict):
    return [{"text": payload[0], "confidence": payload[1]}]


def generate_hypothesis(payload: List) -> Dict:
    """
    Helper function to generate a single hypothesis from the payload.
    """
    hypothesis = {"text": payload[0], "confidence": payload[1]}

    if len(payload) >= 4:
        hypothesis["human_attributes"] = payload[2]
        hypothesis["bot_attributes"] = payload[3]

    if len(payload) == 3 or len(payload) == 5:
        attributes = payload[-1]
        assert isinstance(attributes, dict), "Attribute is a dictionary"
        hypothesis.update(attributes)

    return hypothesis


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
    result = []
    if isinstance(payload[0], list) and isinstance(payload[1], list):
        # several hypotheses from this skill
        for hyp in zip(*payload):
            if hyp[0] and hyp[1] > 0.0:
                result.append(generate_hypothesis(hyp))
    else:
        # only one hypothesis from this skill
        if payload[0] and payload[1] > 0.0:
            result.append(generate_hypothesis(payload))

    return result


def last_utt_sentseg_segments_dialog(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        ["sentences"],
        additional_params={
            "annotation_type": "sentseg",
            "default_result": [dialog["human_utterances"][-1]["text"]],
            "utterance_type": "human_utterances",
        },
    )


def ner_formatter_dialog(dialog: Dict):
    return utils.dream_formatter(
        dialog,
        ["last_utterances"],
        additional_params={
            "annotation_type": "sentseg",
            "default_result": [dialog["human_utterances"][-1]["text"]],
            "utterance_type": "human_utterances",
        },
    )


def ner_formatter_last_bot_dialog(dialog: Dict):
    if len(dialog["bot_utterances"]):
        return utils.dream_formatter(
            dialog,
            ["last_utterances"],
            additional_params={
                "annotation_type": "sentseg",
                "default_result": [dialog["bot_utterances"][-1]["text"]],
                "utterance_type": "bot_utterances",
            },
        )
    else:
        return utils.dream_formatter(
            dialog,
            ["get_annotation"],
            additional_params={
                "annotation_type": "sentseg",
                "default_result": [""],
                "utterance_type": "bot_utterances",
            },
        )


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

