from typing import Dict
import logging
import difflib


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def http_api_output_formatter(payload: Dict):
    response = payload["utterances"][-1]["text"]
    active_skill = payload["utterances"][-1]["active_skill"]
    ssml_tagged_response = []
    for hyp in payload["utterances"][-2]["hypotheses"]:
        if hyp.get("skill_name") == active_skill and hyp.get("ssml_tagged_text"):
            if difflib.SequenceMatcher(None, hyp.get("text", "").split(), response.split()).ratio() > 0.9:
                ssml_tagged_response.append(hyp["ssml_tagged_text"])
    ssml_tagged_response = ssml_tagged_response[-1] if ssml_tagged_response else ""
    ret_val = {
        "user_id": payload["human"]["user_telegram_id"],
        "response": response,
        "ssml_tagged_response": ssml_tagged_response,
        "active_skill": active_skill,
    }
    logger.info(f"http api output {ret_val}")
    return ret_val


def http_debug_output_formatter(payload: Dict):
    response = payload["utterances"][-1]["text"]
    active_skill = payload["utterances"][-1]["active_skill"]
    ssml_tagged_response = []
    for hyp in payload["utterances"][-2]["hypotheses"]:
        if hyp.get("skill_name") == active_skill and hyp.get("ssml_tagged_text"):
            if difflib.SequenceMatcher(None, hyp.get("text", "").split(), response.split()).ratio() > 0.9:
                ssml_tagged_response.append(hyp["ssml_tagged_text"])
    ssml_tagged_response = ssml_tagged_response[-1] if ssml_tagged_response else ""
    ret_val = {
        "user_id": payload["human"]["user_telegram_id"],
        "response": response,
        "active_skill": active_skill,
        "ssml_tagged_response": ssml_tagged_response,
        "debug_output": payload["utterances"][-2]["hypotheses"],
        "attributes": payload["utterances"][-1].get("attributes", {}),
    }

    logger.info(f"http api output {ret_val}")
    return ret_val
