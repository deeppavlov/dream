from typing import List, Any


def base_input_formatter(state: List):
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
    last_utts = []
    annotations_histories = []
    last_annotations = []
    dialog_ids = []
    user_ids = []

    for dialog in state:
        utterances_history = []
        annotations_history = []
        for utterance in dialog['utterances']:
            utterances_history.append(utterance['text'])
            annotations_history.append(utterance['annotations'])

        last_utts.append(utterances_history[-1])
        utterances_histories.append(utterances_history)
        last_annotations.append(annotations_history[-1])
        annotations_histories.append(annotations_history)

        dialog_ids.append(dialog['id'])
        user_ids.extend([utt['user']['id'] for utt in state[0]['utterances']])

    return {'dialogs': state,
            'last_utterances': last_utts,
            'last_annotations': last_annotations,
            'utterances_histories': utterances_histories,
            'annotation_histories': annotations_histories,
            'dialog_ids': dialog_ids,
            'user_ids': user_ids}


def last_utterances(payload, model_args_names):
    utterances = base_input_formatter(payload)['last_utterances']
    return {model_args_names[0]: utterances}


def base_skill_output_formatter(payload):
    """Works with a single batch instance

    Args:
       payload: one batch instance

    Returns: a formatted batch instance

    """
    return {"text": payload[0],
            "confidence": payload[1]}


def base_annotator_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return payload


def ner_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return {'tokens': payload[0],
                'tags': payload[1]}


def sentiment_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return [el for el in payload]


def chitchat_odqa_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        response = []
        for el in payload:
            class_name = el[0]
            if class_name in ['speech', 'negative']:
                response.append('chitchat')
            else:
                response.append('odqa')
        return response


def odqa_formatter(payload: Any, model_args_names=('question_raw',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return {"text": payload[0],
                "confidence": 0.5}


def chitchat_formatter(payload: Any, model_args_names=('q',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    elif mode == 'out':
        return {"text": payload[0],
                "confidence": 0.5}


def chitchat_example_formatter(payload: Any,
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
