from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

LAST_N_TURNS = 5  # number of turns to consider in annotator/skill.


def alice_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: alice_formatter
    last_n_sents = 5
    human_utts = [utt['annotations']['sentseg']['punct_sent']
                  for utt in dialog['utterances'] if utt['user']['user_type'] == 'human']
    return [{'sentences_batch': [human_utts[-last_n_sents:]]}]


def eliza_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: eliza_formatter
    history = []
    prev_human_utterance = None
    for utt in dialog['utterances']:
        if utt["user"]["user_type"] == "human":
            prev_human_utterance = utt['text']
        elif utt["user"]["user_type"] == "bot" and utt["active_skill"] == "eliza" and prev_human_utterance is not None:
            history.append(prev_human_utterance)
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


def get_last_n_turns(dialog: Dict):
    dialog["utterances"] = dialog["utterances"][-(LAST_N_TURNS * 2 + 1):]
    dialog["human_utterances"] = dialog["human_utterances"][-(LAST_N_TURNS + 1):]
    dialog["bot_utterances"] = dialog["bot_utterances"][-LAST_N_TURNS:]
    return dialog


def replace_with_annotated_utterances(dialog, mode="punct_sent"):
    if mode == "punct_sent":
        for utt in dialog['utterances']:
            utt['text'] = utt['annotations']['sentseg']['punct_sent']
        j = 0
        for i, utt in enumerate(dialog['utterances']):
            if utt['user']['user_type'] == 'human':
                dialog['human_utterances'][j]["text"] = utt['annotations']['sentseg']['punct_sent']
                j += 1
    elif mode == "segments":
        for i, utt in enumerate(dialog['utterances']):
            utt['text'] = utt['annotations']['sentseg']['segments']
        j = 0
        for i, utt in enumerate(dialog['utterances']):
            if utt['user']['user_type'] == 'human':
                dialog['human_utterances'][j]["text"] = utt['annotations']['sentseg']['segments']
                j += 1
        j = 0
        for i, utt in enumerate(dialog['utterances']):
            if utt['user']['user_type'] == 'bot':
                dialog['bot_utterances'][j]["text"] = utt['annotations']['sentseg']['segments']
                j += 1
    return dialog


def base_skill_selector_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: base_skill_selector_formatter
    dialog = get_last_n_turns(dialog)
    dialog = replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{"states_batch": [dialog]}]


def transfertransfo_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: transfertransfo_formatter
    dialog = get_last_n_turns(dialog)
    return [{
        'utterances_histories': [
            [utt['annotations']["sentseg"]["punct_sent"] for utt in dialog['utterances']]
        ],
        'personality': [dialog['bot']['persona']]
    }]


def convert_formatter_dialog(dialog: Dict) -> Dict:
    dialog = get_last_n_turns(dialog)
    return [{
        'utterances_histories': [
            [utt['annotations']["sentseg"]["punct_sent"] for utt in dialog['utterances']]
        ],
        'personality': [dialog['bot']['persona']],
        'topics': [dialog["utterances"][-1]["annotations"]["cobot_topics"]]
    }]


def personality_catcher_formatter_dialog(dialog: Dict) -> Dict:
    # Used by: personality_catcher_formatter
    dialog = get_last_n_turns(dialog)
    return [{'personality': [dialog['utterances'][-1]['text']]}]


def telegram_selector_formatter_in(dialog: Dict):
    dialog = get_last_n_turns(dialog)
    return [dialog['human']['attributes']['active_skill']]


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
    dialog = get_last_n_turns(dialog)
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
    dialog = get_last_n_turns(dialog)
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
    dialog = get_last_n_turns(dialog)
    return [{'speeches': [dialog['utterances'][-1].get('attributes', {}).get('speech', {})]}]


def last_utt_dialog(dialog: Dict) -> Dict:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    dialog = get_last_n_turns(dialog)
    return [{'sentences': [dialog['utterances'][-1]['text']]}]


def last_utt_and_history_dialog(dialog: Dict) -> List:
    # Used by: topicalchat retrieval skills
    dialog = get_last_n_turns(dialog)
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
    dialog = get_last_n_turns(dialog)
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentseg']['punct_sent']
    for i, utt in enumerate(dialog['human_utterances']):
        utt['text'] = dialog["utterances"][i * 2]['annotations']['sentseg']['punct_sent']
    return [{'dialogs': [dialog]}]


def full_utt_sentseg_punct_dialog(dialog: Dict):
    '''
    Used ONLY by: base_response_selector_formatter
    '''
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentseg']['punct_sent']
    for i, utt in enumerate(dialog['human_utterances']):
        utt['text'] = dialog["utterances"][i * 2]['annotations']['sentseg']['punct_sent']
    return [{'dialogs': [dialog]}]


def utt_sentrewrite_modified_last_dialog(dialog: Dict):
    # Used by: book_skill_formatter; misheard_asr_formatter, cobot_qa_formatter
    dialog = get_last_n_turns(dialog)
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentrewrite']['modified_sents'][-1]
    for i, utt in enumerate(dialog['human_utterances']):
        utt['text'] = dialog["utterances"][i * 2]['annotations']['sentrewrite']['modified_sents'][-1]
    return [{'dialogs': [dialog]}]


def skill_with_attributes_formatter_service(payload: Dict):
    # Used by: book_skill_formatter, skill_with_attributes_formatter, news_skill, meta_script_skill
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
    dialog = get_last_n_turns(dialog)
    return [{'sentences': [dialog['utterances'][-1]['annotations']['sentseg']['punct_sent']]}]


def last_utt_sentseg_segments_dialog(dialog: Dict):
    # Used by: intent_catcher_formatter
    dialog = get_last_n_turns(dialog)
    return [{'sentences': [dialog['utterances'][-1]['annotations']['sentseg']['segments']]}]


def ner_formatter_dialog(dialog: Dict):
    # Used by: ner_formatter
    dialog = get_last_n_turns(dialog)
    return [{'last_utterances': [dialog['utterances'][-1]['annotations']['sentseg']['segments']]}]


def reddit_ner_formatter_dialog(dialog: Dict):
    # Used by: reddit_ner_skill
    dialog = get_last_n_turns(dialog)
    return [
        {
            'sentiment': [dialog['utterances'][-1]['annotations']['sentiment_classification']],
            'intent': [dialog['utterances'][-1]['annotations']['intent_catcher']],
            'ner': [dialog['utterances'][-1]['annotations']['ner']],
            'continuation': [0 if len(dialog['utterances']) < 2
                             else int(dialog['utterances'][-2]['active_skill'] == 'reddit_ner_skill')]
        }
    ]


def intent_responder_formatter_dialog(dialog: Dict):
    # Used by: intent_responder
    intents = list(dialog['utterances'][-1]['annotations']['intent_catcher'].keys())
    called_intents = {intent: False for intent in intents}
    for utt in dialog['human_utterances'][:-1]:
        called = [intent for intent, value in utt['annotations'].get('intent_catcher', {}).items() if value['detected']]
        for intent in called:
            called_intents[intent] = True
    dialog['called_intents'] = called_intents
    dialog["utterances"] = dialog["utterances"][-(LAST_N_TURNS * 2 + 1):]
    for utt in dialog['utterances']:
        utt['text'] = utt['annotations']['sentseg']['punct_sent']
    return [{'dialogs': [dialog]}]


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
