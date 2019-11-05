from typing import Dict


def http_api_output_formatter(payload: Dict):
    return {
        'user_id': payload['dialog']['human']['user_telegram_id'],
        'response': payload['dialog']['utterances'][-1]['text'],
        'active_skill': payload['dialog']['utterances'][-1]['active_skill']
    }


def http_debug_output_formatter(payload: Dict):
    return {
        'user_id': payload['dialog']['human']['user_telegram_id'],
        'response': payload['dialog']['utterances'][-1]['text'],
        'active_skill': payload['dialog']['utterances'][-1]['active_skill'],
        'debug_output': payload['dialog']['utterances'][-2]['hypotheses']
    }
