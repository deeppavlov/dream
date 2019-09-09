from typing import Dict, Any, List
import copy

CMDS = ["/new_persona"]  # TODO: rm crutch of personality_catcher

# TODO: rm crutch of personality_catcher
def exclude_cmds(utter, cmds):
    if cmds:
        utter = utter.replace(cmds[-1],'')
        return exclude_cmds(utter, cmds[:-1])
    else:
        return utter

# TODO: rm crutch of personality_catcher
def commands_excluder(utters_batch: List, cmds=[]):
    cmds = cmds if cmds else CMDS
    out_batch = []
    for utters in utters_batch:
        out_batch.append([exclude_cmds(ut, cmds) for ut in utters])
    return out_batch

def base_input_formatter(state: Dict, cmd_exclude=True):
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
    user_telegram_ids = []

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
        # USER ID, который вводится в console.run - это user_telegram_id  ¯\_(ツ)_/¯ 
        user_telegram_ids.append(dialog['user']['user_telegram_id'])

    return {'dialogs': state['dialogs'],
            'last_utterances': last_utterances,
            'last_annotations': last_annotations,
            # TODO: rm crutch of personality_catcher
            'utterances_histories': commands_excluder(utterances_histories) if cmd_exclude else utterances_histories,
            'annotation_histories': annotations_histories,
            'dialog_ids': dialog_ids,
            'user_ids': user_ids,
            'user_telegram_ids': user_telegram_ids}


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

# TODO: rm crutch of personality_catcher
default_persona = [
    "i prefer vinyl records to any other music recording format.",
    "i fix airplanes for a living.",
    "drive junk cars that no one else wants.",
    "i think if i work hard enough i can fix the world.",
    "i am never still."
]

# TODO: rm crutch of personality_catcher
def get_persona(dialog):
    try:
        hypts = [ut.get('selected_skills', {}).get('personality_catcher', {}).get('personality') for ut in dialog['utterances'][:-1]]
    except Exception:
        hypts = []
    hypts = [hypt for hypt in hypts if hypt]
    return hypts[-1] if hypts else default_persona


def transfertransfo_formatter(payload: Any, mode='in'):
    if mode == 'in':
        parsed = base_input_formatter(payload)
        return {'utterances_histories': parsed['utterances_histories'],
                'personality': [get_persona(dialog) for dialog in parsed['dialogs']]}
    elif mode == 'out':
        return base_skill_output_formatter(payload)

# TODO: rm crutch of personality_catcher
def personality_catcher_formatter(payload: Any, mode='in'):
    if mode == 'in':
        parsed = base_input_formatter(payload, cmd_exclude=False)
        return {'personality': parsed['last_utterances']}
    elif mode == 'out':
        response = base_skill_output_formatter(payload)
        response['personality'] = payload[2]
        return response


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
        user_ids = inp_data['user_telegram_ids']
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


def sent_segm_formatter(payload, mode='in'):
    if mode == 'in':
        sentences = base_input_formatter(payload)['last_utterances']
        return {'sentences': sentences}
    elif mode == 'out':
        return payload
