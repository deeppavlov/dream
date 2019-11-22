from typing import Dict
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def http_api_output_formatter(payload: Dict):
    ret_val = {
        'user_id': payload['human']['user_telegram_id'],
        'response': payload['utterances'][-1]['text'],
        'active_skill': payload['utterances'][-1]['active_skill']
    }
    logger.info(f"http api output {ret_val}")
    return ret_val


def http_debug_output_formatter(payload: Dict):
    ret_val = {
        'user_id': payload['human']['user_telegram_id'],
        'response': payload['utterances'][-1]['text'],
        'active_skill': payload['utterances'][-1]['active_skill'],
        'debug_output': payload['utterances'][-2]['hypotheses']
    }

    logger.info(f"http api output {ret_val}")
    return ret_val
