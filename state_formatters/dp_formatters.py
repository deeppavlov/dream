from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def alice_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: alice_formatter
    last_n_sents = 5
    human_utts = [utt['annotations']['sentseg']['punct_sent']
                  for utt in dialog['utterances'] if utt['user']['user_type'] == 'human']
    return [{'sentences_batch': [human_utts[-last_n_sents:]]}]


def eliza_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: eliza_formatter
    history = []
    for last_utter, next_utter in zip(dialog["utterances"][::2], dialog["utterances"][1::2]):
        is_human = last_utter["user"]["user_type"] == "human"
        is_bot = next_utter["user"]["user_type"] == "bot"
        is_eliza = next_utter["active_skill"] == "eliza"
        if is_human and is_bot and is_eliza:
            history.append(last_utter["text"])
    return [{
        "last_utterance_batch": [dialog['utterances'][-1]['text']],
        "human_utterance_history_batch": [history],
    }]


def aiml_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: aiml_formatter
    return [{
        'states_batch': [{'user_id': dialog['human']['id']}],
        'utterances_batch': [dialog['utterances'][-1]['text']]
    }]


def cobot_qa_formatter_service(payload):
    # Used by: cobot_qa_formatter
    hyps = []
    for resp, conf in zip(payload[0], payload[1]):
        hyps.append({"text": resp, "confidence": conf})
    return hyps


def misheard_asr_formatter_service(payload):
    # Used by: misheard_asr_formatter
    hyps = []
    for resp, conf, ha, ba in zip(payload[0], payload[1], payload[2], payload[3]):
        hyps.append({"text": resp, "confidence": conf, "human_attributes": ha, "bot_attributes": ba})
    return hyps


def base_skill_selector_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: base_skill_selector_formatter
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentseg']['punct_sent']
    return [{"states_batch": [dialog]}]


def transfertransfo_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: transfertransfo_formatter
    return [{
        'utterances_histories': [
            [utt['annotations']["sentseg"]["punct_sent"] for utt in dialog['utterances']]
        ],
        'personality': [dialog['bot']['persona']]
    }]


def convert_formatter_dialog(dialog: Dict) -> Dict:
    return [{
        'utterances_histories': [
            [utt['annotations']["sentseg"]["punct_sent"] for utt in dialog['utterances']]
        ],
        'personality': [dialog['bot']['persona']],
        'topics': [dialog["utterances"][-1]["annotations"]["cobot_topics"]]
    }]


def personality_catcher_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: personality_catcher_formatter
    return [{'personality': [dialog['utterances'][-1]['text']]}]


def personality_catcher_formatter_service(payload: List):
    # Used by: personality_catcher_formatter
    return [{
        'text': payload[0],
        'confidence': payload[1],
        'personality': payload[2],
        'bot_attributes': {'persona': payload[2]}
    }]


def cobot_classifiers_formatter_service(payload: List):
    # Used by: cobot_classifiers_formatter, sentiment_formatter
    if len(payload) == 3:
        return {"text": payload[0],
                "confidence": payload[1],
                "is_blacklisted": payload[2]}
    elif len(payload) == 2:
        return {"text": payload[0],
                "confidence": payload[1]}
    elif len(payload) == 1:
        return {"text": payload[0]}
    elif len(payload) == 0:
        return {"text": []}


def cobot_dialogact_formatter_service(payload: List):
    # Used by: cobot_dialogact_formatter
    return {"intents": payload[0],
            "topics": payload[1]}


def cobot_formatter_dialog(dialog: Dict):
    # Used by: cobot_dialogact_formatter, cobot_classifiers_formatter
    utterances_histories = []
    for utt in dialog['utterances']:
        utterances_histories.append(utt['annotations']['sentseg']['segments'])
    return [{'utterances_histories': [utterances_histories]}]


def base_response_selector_formatter_service(payload: List):
    # Used by: base_response_selector_formatter

    if len(payload) == 3:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2]}
    elif len(payload) == 5:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2],
                "human_attributes": payload[3], "bot_attributes": payload[4]}


def sent_rewrite_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: sent_rewrite_formatter
    utterances_histories = []
    annotation_histories = []
    for utt in dialog['utterances']:
        annotation_histories.append(utt['annotations'])
        utterances_histories.append(utt['annotations']['sentseg']['segments'])
    return [{
        'utterances_histories': [utterances_histories],
        'annotation_histories': [annotation_histories]
    }]


def asr_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: asr_formatter
    return [{'speeches': [dialog['utterances'][-1].get('attributes', {}).get('speech', {})]}]


def last_utt_dialog(dialog: Dict) -> Dict:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    return [{'sentences': [dialog['utterances'][-1]['text']]}]


def last_utt_and_history_dialog(dialog: Dict) -> List:
    # Used by: topicalchat retrieval skills
    return [{
        'sentences': [dialog['utterances'][-1]['text']],
        'utterances_histories': [[utt['annotations']['sentseg']['punct_sent'] for utt in dialog['utterances']]]
    }]


def dp_toxic_formatter_service(payload: List):
    # Used by: dp_toxic_formatter
    return payload[0]


def base_formatter_service(payload: Dict) -> Dict:
    '''
    Used by: dummy_skill_formatter, intent_responder_formatter, transfertransfo_formatter,
    aiml_formatter, alice_formatter, tfidf_formatter
    '''
    return [{"text": payload[0], "confidence": payload[1]}]


def simple_formatter_service(payload: List):
    '''
    Used by: punct_dialogs_formatter, intent_catcher_formatter, asr_formatter,
    sent_rewrite_formatter, sent_segm_formatter, base_skill_selector_formatter
    '''
    return payload


def utt_sentseg_punct_dialog(dialog: Dict):
    '''
    Used by: skill_with_attributes_formatter; punct_dialogs_formatter,
    dummy_skill_formatter, base_response_selector_formatter
    '''
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentseg']['punct_sent']
    return [{'dialogs': [dialog]}]


def utt_sentrewrite_modified_last_dialog(dialog: Dict):
    # Used by: book_skill_formatter; misheard_asr_formatter, cobot_qa_formatter
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentrewrite']['modified_sents'][-1]
    return [{'dialogs': [dialog]}]


def skill_with_attributes_formatter_service(payload: Dict):
    # Used by: book_skill_formatter, skill_with_attributes_formatter, news_skill
    if len(payload) == 3:
        result = {"text": payload[0],
                  "confidence": payload[1]}
        for key in payload[2]:
            result[key] = payload[2][key]
        return [result]
    elif len(payload) == 4:
        return [{
            "text": payload[0],
            "confidence": payload[1],
            "human_attributes": payload[2],
            "bot_attributes": payload[3]
        }]
    elif len(payload) == 5:
        # payload[4] is a dictionary with additional keys-labels-annotations to the reply
        # payload[4] = {"any_key" : "any_value"}
        # for example, movie-skill
        # Dp-formatter for movie-skill:
        # {
        #   'text': "It's a pleasure to know you better. I adore Brad Pitt!",
        #   'confidence': 0.98, 'human_attributes': {}, 'bot_attributes': {},
        #   'bot_attitudes': [['Brad Pitt', 'actor', 'very_positive']],
        #   'human_attitudes': [['Brad Pitt', 'actor', 'positive']]
        # }
        result = {
            "text": payload[0],
            "confidence": payload[1],
            "human_attributes": payload[2],
            "bot_attributes": payload[3]
        }
        for key in payload[4]:
            result[key] = payload[4][key]
        return [result]
    else:
        return [{
            "text": payload[0],
            "confidence": payload[1]
        }]


def last_utt_sentseg_punct_dialog(dialog: Dict):
    # Used by: attitude_formatter, sentiment_formatter
    return [{'sentences': [dialog['utterances'][-1]['annotations']['sentseg']['punct_sent']]}]


def last_utt_sentseg_segments_dialog(dialog: Dict):
    # Used by: intent_catcher_formatter
    return [{'sentences': [dialog['utterances'][-1]['annotations']['sentseg']['segments']]}]


def ner_formatter_dialog(dialog: Dict):
    # Used by: ner_formatter
    return [{'last_utterances': [dialog['utterances'][-1]['annotations']['sentseg']['segments']]}]


def attitude_formatter_service(payload: Dict):
    # Used by: attitude_formatter
    payload = payload[0]
    if len(payload) == 2:
        return {"text": payload[0],
                "confidence": payload[1]}
    elif len(payload) == 1:
        return {"text": payload[0]}
    elif len(payload) == 0:
        return {"text": []}
