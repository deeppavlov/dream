from typing import Dict


def base_state_formatter(state: Dict):
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

    return {'last_utterances': last_utterances,
            'last_annotations': last_annotations,
            'utterances_histories': utterances_histories,
            'annotation_histories': annotations_histories,
            'dialog_ids': dialog_ids,
            'user_ids': user_ids}


def obscenity_formatter(state: Dict, model_args_names=('context',)):
    last_utterances = base_state_formatter(state)['last_utterances']
    payload = {model_args_names[0]: last_utterances}
    return payload


FORMATTERS = {"obscenity": obscenity_formatter}


