from typing import Dict, Any


def base_input_formatter(state: Dict):
    """This state_formatter takes the most popular fields from Agent state and returns them as dict values:
        * last utterances: a list of last utterance from each dialog in the state
        * last_annotations: a list of last annotation from each last utterance
        * utterances_histories: a list of lists of all utterances from all dialogs
        * annotations_histories: a list of lists of all annotations from all dialogs
        * dialog_ids: a list of all dialog ids
        * user_ids: a list of all user ids, each dialog have a unique human participant id
    Args:
        state: dialog state

    Returns: formatted dialog state

    """
    utterances_histories = []
    last_utterances = []
    annotations_histories = []
    last_annotations = []
    dialog_ids = []
    user_ids = []

    for dialog in state['dialogs']:
        utterances_history = []
        annotations_history = []
        for utterance in dialog['utterances']:
            utterances_history.append(utterance['text'])
            annotations_history.append(utterance['annotations'])

        last_utterances.append(utterances_history[-1])
        utterances_histories.append(utterances_history)
        last_annotations.append(annotations_history[-1])
        annotations_histories.append(annotations_history)

        dialog_ids.append(dialog['id'])
        user_ids.append(dialog['user']['id'])

    return {'dialogs': state['dialogs'],
            'last_utterances': last_utterances,
            'last_annotations': last_annotations,
            'utterances_histories': utterances_histories,
            'annotation_histories': annotations_histories,
            'dialog_ids': dialog_ids,
            'user_ids': user_ids}


def last_utterances(payload, model_args_names):
    utterances = base_input_formatter(payload)['last_utterances']
    return {model_args_names[0]: utterances}


def base_skill_output_formatter(payload):
    return {"text": payload[0],
            "confidence": payload[1]}


def base_annotator_formatter(payload: Any, model_args_names=('context',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return payload


def ner_formatter(payload: Any, model_args_names=('context',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return {'tokens': payload[0],
                'tags': payload[1]}


def sentiment_formatter(payload: Any, model_args_names=('context',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return [el[0] for el in payload]


def chitchat_odqa_formatter(payload: Any, model_args_names=('context',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        response = []
        for el in payload:
            class_name = el[0][0]
            if class_name in ['speech', 'negative']:
                response.append('chitchat')
            else:
                response.append('odqa')
        return response


def odqa_formatter(payload: Any, model_args_names=('context',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return {"text": payload[0],
                "confidence": 0.5}


def chitchat_formatter(payload: Any,
                       model_args_names=("utterances", 'annotations', 'u_histories', 'dialogs'),
                       mode='in'):
    if mode == 'in':
        parsed = base_input_formatter(payload)
        return {model_args_names[0]: parsed['last_utterances'],
                model_args_names[1]: parsed['last_annotations'],
                model_args_names[2]: parsed['utterances_histories'],
                model_args_names[3]: parsed['dialogs']}
    elif mode == 'out':
        return {"text": payload[0],
                "confidence": payload[1],
                "name": payload[2]}


def alice_formatter(payload, mode='in'):
    if mode == 'in':
        sents = [u['text'] for u in payload['dialogs'][-1]['utterances']]
        last_n_sents = 5
        # Send only last n sents of the latest dialogue
        sents = sents[-last_n_sents:]
        return {'sentences': sents}
    elif mode == 'out':
        # TODO: how to deal with confidence?
        return base_skill_output_formatter(payload)


def aiml_formatter(payload, mode='in'):
    if mode == 'in':
        sents = [u['text'] for u in payload['dialogs'][-1]['utterances']]
        users = [u['user_id'] for u in payload['dialogs'][-1]['utterances']]
        return {
            'states_batch': [{'user_id': users[-1]}],
            'utterances_batch': [sents[-1]]
        }
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def cobot_qa_formatter(payload, mode='in'):
    if mode == 'in':
        sentences = base_input_formatter(payload)['last_utterances']
        return {'sentences': sentences}
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def base_skill_selector_formatter(payload: Any, mode='in'):
    if mode == 'in':
        return {"states_batch": payload['dialogs']}
    elif mode == 'out':
        # it's questionable why output from Model itself is 2dim: batch size x n_skills
        # and payload here is 3dim. I don't know which dim is extra and from where it comes
        return payload[0]


def transfertransfo_formatter(payload: Any, mode='in'):
    if mode == 'in':
        parsed = base_input_formatter(payload)
        return {'utterances_histories': parsed['utterances_histories'],
                'personality': [dialog['bot']['persona'] for dialog in parsed['dialogs']]}
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def cobot_offensiveness_formatter(payload, mode='in'):
    if mode == 'in':
        sentences = base_input_formatter(payload)['last_utterances']
        return {'sentences': sentences}
    elif mode == 'out':
        return {"text": payload[0],
                "confidence": payload[1],
                "is_blacklisted": payload[2]}


def cobot_dialogact_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = base_input_formatter(payload)['dialogs']
        return {"dialogs": dialogs}
    elif mode == 'out':
        return {"text": payload[0]}


def program_y_formatter(payload, mode='in'):
    if mode == 'in':
        inp_data = base_input_formatter(payload)
        sentences = inp_data['last_utterances']
        user_ids = inp_data['user_ids']
        return {'sentences': sentences, 'user_ids': user_ids}
    elif mode == 'out':
        return {"text": payload[0],
                "confidence": payload[1]}


def base_response_selector_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = base_input_formatter(payload)['dialogs']
        return {"dialogs": dialogs}
    elif mode == 'out':
        return payload