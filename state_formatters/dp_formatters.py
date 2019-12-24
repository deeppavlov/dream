from typing import Dict, Any, List
from .utils import commands_excluder


def base_input_formatter(state: List, cmd_exclude=True):
    """This state_formatter takes the most popular fields from Agent state and returns them as dict values:
        * last utterances: a list of last utterance from each dialog in the state
        * last_annotations: a list of last annotation from each last utterance
        * utterances_histories: a list of lists of all utterances from all dialogs
        * annotations_histories: a list of lists of all annotations from all dialogs
        * dialog_ids: a list of all dialog ids
        * user_ids: a list of all user ids, each dialog have a unique human participant id
    Args:
        state: dialog state
        cmd_exclude: a bool, set True to exclude commands from utterances_histories

    Returns: formatted dialog state

    """
    utterances_histories = []
    last_utts = []
    annotations_histories = []
    last_annotations = []
    dialog_ids = []
    user_ids = []
    user_telegram_ids = []

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
        # USER ID, который вводится в console.run - это user_telegram_id  ¯\_(ツ)_/¯
        user_telegram_ids.extend([utt['user']['user_telegram_id']
                                  if utt['user']["user_type"] == "human" else None
                                  for utt in state[0]['utterances']])

    return {'dialogs': state,
            'last_utterances': last_utts,
            'last_annotations': last_annotations,
            'utterances_histories': commands_excluder(utterances_histories) if cmd_exclude else utterances_histories,
            'annotation_histories': annotations_histories,
            'dialog_ids': dialog_ids,
            'user_ids': user_ids,
            'user_telegram_ids': user_telegram_ids}


def last_utterances(payload, model_args_names):
    utterances = base_input_formatter(payload)['last_utterances']
    return {model_args_names[0]: utterances}


def annotated_input_formatter(state: Dict, cmd_exclude=True, annotation="punctuated"):
    """
    The same function as `base_input_formatter` but all utterances in all returned fields
    could be:
    - texts with added punctuation by `sentseg` annotator (if `annotation="punctuated"`)
    - lists of sentences with punctuation (if `annotation="segmented"`)
    - punctuated texts rewritten (with resolved coref) by `sentrewrite` (if `annotation="coref_resolved"`)

    Args:
        state: dialog state
        cmd_exclude: a bool, set True to exclude commands from utterances_histories
        annotation: `punctuated` or `segmented` or `coref_resolved`

    Returns:
        formatted dialog state.
        In case of `segmented`, returned `dialogs` field DOES NOT contain segments but `punctuated` texts
            while other returned fields contain segments instead of `text`.
    """
    utterances_histories = []
    last_utts = []
    annotations_histories = []
    last_annotations = []
    dialog_ids = []
    user_ids = []
    user_telegram_ids = []

    for dialog in state:
        utterances_history = []
        annotations_history = []
        for utterance in dialog['utterances']:
            try:
                if "bot_sentseg" in utterance["annotations"].keys():
                    prefix = "bot_"
                else:
                    prefix = ""
                if annotation == "punctuated":
                    utterance["text"] = utterance["annotations"][prefix + "sentseg"]["punct_sent"]
                    utterances_history.append(utterance["annotations"][prefix + "sentseg"]["punct_sent"])
                elif annotation == "segmented":
                    utterance["text"] = utterance["annotations"][prefix + "sentseg"]["punct_sent"]
                    utterances_history.append(utterance["annotations"][prefix + "sentseg"]["segments"])
                elif annotation == "coref_resolved":
                    # sentrewrite model annotates k last utterances, we can take only last one or
                    # take all last k utterances from this annotator
                    utterance["text"] = utterance["annotations"][prefix + "sentrewrite"]["modified_sents"][-1]
                    utterances_history.append(utterance["annotations"][prefix + "sentrewrite"]["modified_sents"][-1])
            except KeyError:
                # bot utterances are not annotated
                utterances_history.append(utterance["text"])
            annotations_history.append(utterance['annotations'])

        last_utts.append(utterances_history[-1])
        utterances_histories.append(utterances_history)
        last_annotations.append(annotations_history[-1])
        annotations_histories.append(annotations_history)

        dialog_ids.append(dialog['id'])
        user_ids.extend([utt['user']['id'] for utt in state[0]['utterances']])
        # USER ID, который вводится в console.run - это user_telegram_id  ¯\_(ツ)_/¯
        user_telegram_ids.extend([utt['user']['user_telegram_id']
                                  if utt['user']["user_type"] == "human" else None
                                  for utt in state[0]['utterances']])

    if cmd_exclude:
        if annotation in ["punctuated", "coref_resolved"]:
            utterances_histories = commands_excluder(utterances_histories)
        elif annotation == "segmented":
            utterances_histories = [commands_excluder(utter_list)
                                    for utter_list in utterances_histories]

    return {'dialogs': state,
            'last_utterances': last_utts,
            'last_annotations': last_annotations,
            'utterances_histories': utterances_histories,
            'annotation_histories': annotations_histories,
            'dialog_ids': dialog_ids,
            'user_ids': user_ids,
            'user_telegram_ids': user_telegram_ids}


def base_skill_output_formatter(payload):
    """Works with a single batch instance

    Args:
       payload: one batch instance

    Returns: a formatted batch instance

    """
    return [{"text": payload[0], "confidence": payload[1]}]


def base_annotator_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    if mode == 'out':
        return payload


def tfidf_formatter(payload, mode='in'):
    if mode == 'in':
        sentences = base_input_formatter(payload)['last_utterances']
        return {'sentences': sentences}
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def sentiment_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return {'sentences': annotated_input_formatter(payload, annotation="punctuated")["last_utterances"]}
    elif mode == 'out':
        if len(payload) == 3:
            return {"text": payload[0],
                    "confidence": payload[1],
                    "is_blacklisted": payload[2]}
        elif len(payload) == 2:
            return {"text": payload[0],
                    "confidence": payload[1]}
        elif len(payload) == 1:
            return {"text": payload[0]}


def chitchat_odqa_formatter(payload: Any, model_args_names=('x',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    if mode == 'out':
        class_name = payload[0]
        if class_name in ['speech', 'negative']:
            response = ['chitchat']
        else:
            response = ['odqa']
        return response


def odqa_formatter(payload: Any, model_args_names=('question_raw',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    if mode == 'out':
        return [{"text": payload[0],
                 "confidence": 0.5}]


def chitchat_formatter(payload: Any, model_args_names=('q',), mode='in'):
    if mode == 'in':
        return last_utterances(payload, model_args_names)
    if mode == 'out':
        return [{"text": payload[0],
                 "confidence": 0.5}]


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
        return [{"text": payload[0], "confidence": payload[1], "name": payload[2]}]


def alice_formatter(payload, mode='in'):
    if mode == 'in':
        inp_data = annotated_input_formatter(payload)
        last_n_sents = 5
        batch = []
        for dialog in inp_data['dialogs']:
            user_utts = []
            for utt in dialog['utterances']:
                if utt['user']['user_type'] == "human":
                    user_utts.append(utt['text'])
            batch.append(user_utts[-last_n_sents:])
        return {"sentences_batch": batch}
    elif mode == 'out':
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
        dialogs = annotated_input_formatter(payload, annotation="coref_resolved")['dialogs']
        return {'dialogs': dialogs}
    elif mode == 'out':
        hyps = []
        for resp, conf in zip(payload[0], payload[1]):
            hyps.append({"text": resp, "confidence": conf})
        return hyps


def misheard_asr_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="coref_resolved")['dialogs']
        return {'dialogs': dialogs}
    elif mode == 'out':
        hyps = []
        for resp, conf, ha, ba in zip(payload[0], payload[1], payload[2], payload[3]):
            hyps.append({"text": resp, "confidence": conf, "human_attributes": ha, "bot_attributes": ba})
        return hyps


def base_skill_selector_formatter(payload: Any, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="punctuated")['dialogs']
        return {"states_batch": dialogs}
    elif mode == 'out':
        # it's questionable why output from Model itself is 2dim: batch size x n_skills
        # and payload here is 3dim. I don't know which dim is extra and from where it comes
        return payload


def transfertransfo_formatter(payload: Any, mode='in'):
    if mode == 'in':
        parsed = annotated_input_formatter(payload, annotation="punctuated")
        return {'utterances_histories': parsed['utterances_histories'],
                'personality': [dialog['bot']['persona'] for dialog in parsed['dialogs']]}
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def personality_catcher_formatter(payload: Any, mode='in'):
    if mode == 'in':
        parsed = base_input_formatter(payload, cmd_exclude=False)
        return {'personality': parsed['last_utterances']}
    elif mode == 'out':
        response = base_skill_output_formatter(payload)
        response['personality'] = payload[2]
        response["bot_attributes"] = {"persona": payload[2]}
        return response


def cobot_classifiers_formatter(payload, mode='in'):
    if mode == 'in':
        return {'sentences': annotated_input_formatter(payload, annotation="segmented")["last_utterances"]}
    elif mode == 'out':
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


def cobot_dialogact_formatter(payload, mode='in'):
    if mode == 'in':
        return {'utterances_histories': annotated_input_formatter(
            payload, annotation="segmented")["utterances_histories"]}
    elif mode == 'out':
        return {"intents": payload[0],
                "topics": payload[1]}


def base_response_selector_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="punctuated")['dialogs']
        return {"dialogs": dialogs}
    elif mode == 'out':
        if len(payload) == 3:
            return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2]}
        elif len(payload) == 5:
            return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2],
                    "human_attributes": payload[3], "bot_attributes": payload[4]}


def sent_segm_formatter(payload, mode='in'):
    if mode == 'in':
        sentences = base_input_formatter(payload)['last_utterances']
        return {'sentences': sentences}
    elif mode == 'out':
        return payload


def sent_rewrite_formatter(payload, mode='in'):
    if mode == 'in':
        histories = annotated_input_formatter(payload, annotation="segmented")
        return {"utterances_histories": histories["utterances_histories"],
                "annotation_histories": histories["annotation_histories"]}
    elif mode == 'out':
        return payload


def asr_formatter(payload, mode='in'):
    if mode == 'in':
        inp_data = base_input_formatter(payload)
        speeches = []
        for dialog in inp_data['dialogs']:
            last_utterance = dialog['utterances'][-1]
            # attributes may not exist in utterance object if ONLY user_id and payload is passed to API
            speeches.append(last_utterance.get('attributes', {}).get('speech', {}))
        return {'speeches': speeches}
    elif mode == 'out':
        return payload


def dp_toxic_formatter(payload, mode='in'):
    if mode == 'in':
        sentences = base_input_formatter(payload)['last_utterances']
        return {'sentences': sentences}
    elif mode == 'out':
        return payload[0]


def intent_responder_formatter(payload, mode='in'):
    if mode == 'in':
        inp_data = base_input_formatter(payload)

        user_utterances = inp_data['last_utterances']
        annotations = inp_data['last_annotations']

        bot_utterances = []
        for dialog in inp_data['dialogs']:
            utterances = dialog['utterances']
            bot_utterance = ""
            for utt in utterances[::-1]:
                if utt['user']['user_type'] != "human":
                    bot_utterance = utt['text']
                    break
            bot_utterances.append(bot_utterance)
        return {'annotations': annotations, 'user_utterances': user_utterances, 'bot_utterances': bot_utterances}
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def intent_catcher_formatter(payload, mode='in'):
    if mode == 'in':
        inp_data = base_input_formatter(payload)
        try:
            segmented_sentences = [ann['sentseg']['segments'] for ann in inp_data['last_annotations']]
        except KeyError:
            segmented_sentences = [ann['bot_sentseg']['segments'] for ann in inp_data['last_annotations']]
        return {'sentences': segmented_sentences}
    elif mode == 'out':
        return payload


def dummy_skill_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="punctuated")['dialogs']
        return {"dialogs": dialogs}
    elif mode == 'out':
        return base_skill_output_formatter(payload)


def punct_dialogs_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="punctuated")['dialogs']
        return {"dialogs": dialogs}
    elif mode == 'out':
        return payload


def ner_formatter(payload, mode='in'):
    if mode == 'in':
        return {'last_utterances': annotated_input_formatter(payload, annotation="segmented")["last_utterances"]}
    return payload


def skill_with_attributes_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="punctuated")['dialogs']
        # import json
        # print(json.dumps(dialogs, indent=2))
        return {"dialogs": dialogs}
    elif mode == 'out':
        if len(payload) == 4:
            return [{"text": payload[0],
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
            result = {"text": payload[0],
                      "confidence": payload[1],
                      "human_attributes": payload[2],
                      "bot_attributes": payload[3]
                      }
            for key in payload[4]:
                result[key] = payload[4][key]
            return [result]
        else:
            return [{"text": payload[0],
                     "confidence": payload[1]
                     }]


def book_skill_formatter(payload, mode='in'):
    if mode == 'in':
        dialogs = annotated_input_formatter(payload, annotation="coref_resolved")['dialogs']
        return {'dialogs': dialogs}
    else:
        return skill_with_attributes_formatter(payload, mode='out')


def attitude_formatter(payload, mode='in'):
    if mode == 'in':
        return {'sentences': annotated_input_formatter(payload, annotation="punctuated")["last_utterances"]}
    elif mode == 'out':
        payload = payload[0]
        if len(payload) == 2:
            return {"text": payload[0],
                    "confidence": payload[1]}
        elif len(payload) == 1:
            return {"text": payload[0]}
        elif len(payload) == 0:
            return {"text": []}
