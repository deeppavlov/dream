import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

LAST_N_TURNS = 5  # number of turns to consider in annotator/skill.


def catcher_formatter(dialog: Dict) -> Dict:
    return [{'x': [dialog['utterances'][-1]['text']]}]


def last_utt_dialog(dialog: Dict) -> Dict:
    return [{'sentences': [dialog['utterances'][-1]['text']]}]


def base_response_selector_formatter_service(payload: List) -> Dict:
    if len(payload) == 3:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2]}
    elif len(payload) == 5:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2],
                "human_attributes": payload[3], "bot_attributes": payload[4]}


def full_dialog(dialog: Dict):
    return [{'dialogs': [dialog]}]


def base_skill_formatter(payload: Dict) -> Dict:
    return [{"text": payload[0], "confidence": payload[1]}]


def simple_formatter_service(payload: List):
    logging.info('answer ' + str(payload))
    return payload


def entity_linking_formatter(payload: List):
    response = []
    for entity_name, wikidata_ids, id_types in zip(*payload):
        item = {
            'entity_name': entity_name,
            'wikidata_ids': [
                {
                    "id": id,
                    "instance_of": instance_of
                }
                for id, instance_of in zip(wikidata_ids, id_types)
            ]
        }
        response.append(item)
    return response


def hypotheses_list(dialog: Dict) -> Dict:
    hypotheses = dialog["utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    return [{'sentences': hypots}]


def programy_formatter_dialog(dialog: Dict) -> List:
    return [{'sentences_batch': [[u['text'] for u in dialog['utterances'][-5:]]]}]


def skill_with_attributes_formatter_service(payload: Dict):
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
    if isinstance(payload[0], list) and isinstance(payload[1], list):
        result = [{"text": hyp[0],
                   "confidence": hyp[1]} for hyp in zip(*payload)]
    else:
        result = [{"text": payload[0],
                   "confidence": payload[1]}]

    if len(payload) >= 4:
        if isinstance(payload[2], dict) and isinstance(payload[3], dict):
            result[0]["human_attributes"] = payload[2]
            result[0]["bot_attributes"] = payload[3]
        elif isinstance(payload[2], list) and isinstance(payload[3], list):
            for i, hyp in enumerate(zip(*payload)):
                result[i]["human_attributes"] = hyp[2]
                result[i]["bot_attributes"] = hyp[3]

    if len(payload) == 3 or len(payload) == 5:
        if isinstance(payload[-1], dict):
            for key in payload[-1]:
                result[0][key] = payload[-1][key]
        elif isinstance(payload[-1], list):
            for i, hyp in enumerate(zip(*payload)):
                for key in hyp[-1]:
                    result[i][key] = hyp[-1][key]

    return result
