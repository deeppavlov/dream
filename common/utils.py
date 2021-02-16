import re
import logging
from os import getenv
from copy import deepcopy
import sentry_sdk
from random import choice

sentry_sdk.init(getenv('SENTRY_DSN'))


def join_words_in_or_pattern(words):
    return "(" + "|".join([r'\b%s\b' % word for word in words]) + ")"


def join_sentences_in_or_pattern(sents):
    return "(" + "|".join(sents) + ")"


other_skills = {'intent_responder', 'program_y_dangerous', 'misheard_asr', 'christmas_new_year_skill',
                'superbowl_skill', 'oscar_skill', 'valentines_day_skill'}
scenario_skills = {'movie_skill', 'personal_info_skill',  # 'short_story_skill',
                   'book_skill', 'weather_skill', 'emotion_skill', 'dummy_skill_dialog',
                   'meta_script_skill', 'coronavirus_skill', 'small_talk_skill',
                   'news_api_skill', 'game_cooperative_skill'}
retrieve_skills = {'cobotqa', 'program_y', 'alice', 'eliza', 'book_tfidf_retrieval',
                   'entertainment_tfidf_retrieval', 'fashion_tfidf_retrieval', 'movie_tfidf_retrieval',
                   'music_tfidf_retrieval', 'politics_tfidf_retrieval', 'science_technology_tfidf_retrieval',
                   'sport_tfidf_retrieval', 'animals_tfidf_retrieval', 'convert_reddit',
                   'topicalchat_convert_retrieval', 'program_y_wide'}

okay_statements = {"Okay.", "That's cool!", "Interesting.", "Sounds interesting.", "Sounds interesting!",
                   "OK.", "Cool!", "Thanks!", "Okay, thanks.", "I'm glad you think so!",
                   "Sorry, I don't have an answer for that!", "Let's talk about something else.",
                   "As you wish.", "All right.", "Right.", "Anyway.", "Oh, okay.", "Oh, come on.",
                   "Really?", "Okay. I got it.", "Well, okay.", "Well, as you wish."}

service_intents = {'lets_chat_about', 'tell_me_more', 'topic_switching', 'yes', 'opinion_request', 'dont_understand',
                   'no', 'stupid', 'weather_forecast_intent', 'doing_well', 'tell_me_a_story',
                   'what_are_you_talking_about'}
low_priority_intents = {'dont_understand'}

combined_classes = {
    'emotion_classification': ['anger', 'fear', 'joy', 'love', 'sadness', 'surprise', 'neutral'],
    'toxic_classification': ['identity_hate', 'insult',
                             'obscene', 'severe_toxic',
                             'sexual_explicit', 'threat',
                             'toxic'],
    'sentiment_classification': ['positive', 'negative', 'neutral'],
    'cobot_topics': ['Phatic', 'Other', 'Movies_TV', 'Music', 'SciTech', 'Literature',
                     'Travel_Geo', 'Celebrities', 'Games', 'Pets_Animals', 'Sports',
                     'Psychology', 'Religion', 'Weather_Time', 'Food_Drink', 'Politics',
                     'Sex_Profanity', 'Art_Event', 'Math', 'News', 'Entertainment', 'Fashion'],
    'cobot_dialogact_topics': ['Other', 'Phatic', 'Entertainment_Movies', 'Entertainment_Books',
                               'Entertainment_General', 'Interactive', 'Entertainment_Music',
                               'Science_and_Technology', 'Sports', 'Politics'],
    'cobot_dialogact_intents': ['Information_DeliveryIntent', 'General_ChatIntent',
                                'Information_RequestIntent', 'User_InstructionIntent',
                                'InteractiveIntent',
                                'Opinion_ExpressionIntent', 'OtherIntent', 'ClarificationIntent',
                                'Topic_SwitchIntent', 'Opinion_RequestIntent',
                                'Multiple_GoalsIntent']
}


def get_skill_outputs_from_dialog(utterances, skill_name, activated=False):
    """
    Extract list of dictionaries with already formatted outputs of `skill_name` from full dialog.
    If `activated=True`, skill also should be chosen as `active_skill`;
    otherwise, empty list.

    Args:
        utterances: utterances, the first one is user's reply
        skill_name: name of target skill
        activated: if target skill should be chosen by response selector on previous step or not

    Returns:
        list of dictionaries with formatted outputs of skill
    """
    result = []

    skills_outputs = []
    for uttr in utterances:
        if "active_skill" in uttr:
            final_response = uttr.get("orig_text", None) if uttr.get("orig_text", None) is not None else uttr["text"]
            for skop in skills_outputs:
                # need to check text-response for skills with several hypotheses
                if skop["skill_name"] == skill_name:
                    if activated and skop["text"] in final_response and uttr["active_skill"] == skill_name:
                        # removed one condition as if scop contains skill_name and text, its len is > 0
                        result.append(skop)
                    else:
                        if not activated and len(skop) > 0:
                            result.append(skop)
        elif "hypotheses" in uttr:
            skills_outputs = uttr["hypotheses"]

    return result


def transform_vbg(s):
    """
    Transform infinitive form of verb to Ving form.

    Args:
        s: verb infinitive

    Returns:
        string with required verb form
    """
    import re

    # by Anastasia Kravtsova
    s += '+VBG'
    # irregular cases
    s1 = re.compile(r'(?<![a-z])be\+VBG')
    s2 = re.compile(r'(?<![aouiey])([^aouiey][aouiey]([^aouieywr]))\+VBG')
    s3 = re.compile(r'ie\+VBG')
    s4 = re.compile(r'(ee)\+VBG')
    s5 = re.compile(r'e\+VBG')
    # regular case
    s6 = re.compile(r"\+VBG")

    # irregular cases
    s = re.sub(s1, 'being', s)
    s = re.sub(s2, r'\1\2ing', s)
    s = re.sub(s3, r'ying', s)
    s = re.sub(s4, r'\1ing', s)
    s = re.sub(s5, r'ing', s)
    # regular case
    s = re.sub(s6, "ing", s)
    return s


def get_list_of_active_skills(utterances):
    """
    Extract list of active skills names

    Args:
        utterances: utterances, the first one is user's reply

    Returns:
        list of string skill names
    """
    result = []

    for uttr in utterances:
        if "active_skill" in uttr:
            result.append(uttr["active_skill"])

    return result


def get_user_replies_to_particular_skill(utterances, skill_name):
    """
    Return user's responses to particular skill if it was active
    Args:
        utterances:
        skill_name:

    Returns:
        list of string response
    """
    result = []
    for i, uttr in enumerate(utterances):
        if uttr.get("active_skill", "") == skill_name:
            result.append(utterances[i - 1]["text"])
    return result


yes_templates = re.compile(r"(\byes\b|\byup\b|\byep\b|\bsure\b|go ahead|\byeah\b|\bok\b|okay|"
                           r"^why not\.?$|^tell me\.?$|^i agree\.?$|^i think so\.?$)")


def is_yes(annotated_phrase):
    yes_detected = annotated_phrase['annotations'].get('intent_catcher', {}).get('yes', {}).get('detected') == 1
    # TODO: intent catcher not catches 'yes thanks!'
    return yes_detected or re.search(yes_templates, annotated_phrase["text"].lower())


no_templates = re.compile(r"(\bno\b|\bnot\b|no way|don't|no please|i disagree)")
DONOTKNOW_LIKE = [r"(i )?(do not|don't) know", "you (choose|decide|pick up)"]


def is_no(annotated_phrase):
    no_detected = annotated_phrase.get("annotations", {}).get('intent_catcher', {}).get('no', {}).get('detected') == 1
    # TODO: intent catcher thinks that horrible is no intent'
    user_phrase = annotated_phrase.get('text', '').lower().strip().replace('.', '')
    is_not_horrible = 'horrible' != user_phrase
    no_regexp_detected = re.search(no_templates, annotated_phrase["text"].lower())
    is_not_idontknow = not re.search(join_sentences_in_or_pattern(DONOTKNOW_LIKE), annotated_phrase["text"].lower())

    return is_not_horrible and (no_detected or no_regexp_detected) and is_not_idontknow


def is_question(text):
    return '?' in text


def substitute_nonwords(text):
    return re.sub(r"\W+", " ", text).strip()


def get_intent_name(text):
    splitter = "#+#"
    if splitter not in text:
        return None
    intent_name = text.split(splitter)[-1]
    intent_name = re.sub(r"\W", " ", intent_name.lower()).strip()
    return intent_name


def is_opinion_request(annotated_phrase):
    annotations = annotated_phrase.get("annotations", {})
    intents = get_intents(annotated_phrase, which="cobot_dialogact_intents")
    intent_detected = annotations.get("intent_catcher", {}).get("opinion_request", {}).get(
        "detected") == 1 or "Opinion_RequestIntent" in intents
    opinion_detected = "Opinion_ExpressionIntent" in intents

    opinion_request_pattern = re.compile(r"(don't|do not|not|are not|are|do)?\s?you\s"
                                         r"(like|dislike|adore|hate|love|believe|consider|get|know|taste|think|"
                                         r"recognize|sure|understand|feel|fond of|care for|fansy|appeal|suppose|"
                                         r"imagine|guess)")
    if intent_detected or \
        (re.search(opinion_request_pattern,
                   annotated_phrase["text"].lower()) and not opinion_detected and "?" in annotated_phrase["text"]):
        return True
    else:
        return False


def get_outputs_with_response_from_dialog(utterances, response, activated=False):
    """
    Extract list of dictionaries with already formatted outputs of different skills from full dialog
    which replies containe `response`.
    If `activated=True`, skill also should be chosen as `active_skill`;
    otherwise, empty list.

    Args:
        utterances: utterances, the first one is user's reply
        response: target text to search among bot utterances
        activated: if target skill should be chosen by response selector on previous step or not

    Returns:
        list of dictionaries with formatted outputs of skill
    """
    result = []

    skills_outputs = []
    for uttr in utterances:
        if "active_skill" in uttr:
            final_response = uttr["text"]
            for skop in skills_outputs:
                # need to check text-response for skills with several hypotheses
                if response in skop["text"]:
                    if activated and skop["text"] in final_response and len(skop) > 0:
                        result.append(skop)
                    else:
                        if not activated and len(skop) > 0:
                            result.append(skop)
        elif "hypotheses" in uttr:
            skills_outputs = uttr["hypotheses"]

    return result


def get_not_used_template(used_templates, all_templates):
    """
    Chooce not used template among all templates

    Args:
        used_templates: list of templates already used in the dialog
        all_templates: list of all available templates

    Returns:
        string template
    """
    available = list(set(all_templates).difference(set(used_templates)))
    if len(available) > 0:
        return choice(available)
    else:
        return choice(all_templates)


def _probs_to_labels(answer_probs, threshold=0.5):
    answer_labels = [label for label in answer_probs if answer_probs[label] > threshold]
    if len(answer_labels) == 0:
        answer_labels = [key for key in answer_probs
                         if answer_probs[key] == max(answer_probs.values())]
    return answer_labels


def _labels_to_probs(answer_labels, all_labels):
    answer_probs = dict()
    for label in all_labels:
        if label in answer_labels:
            answer_probs[label] = 1
        else:
            answer_probs[label] = 0
    return answer_probs


def _get_combined_annotations(annotated_utterance, model_name):
    answer_probs, answer_labels = {}, []
    try:
        annotations = annotated_utterance['annotations']
        combined_annotations = annotations['combined_classification']
        if len(combined_annotations) > 0 and type(combined_annotations) == list:
            combined_annotations = combined_annotations[0]
        if model_name in combined_annotations:
            answer_probs = combined_annotations[model_name]
        else:
            raise Exception(f'Not found Model name {model_name} in combined annotations {combined_annotations}')
        answer_labels = _probs_to_labels(answer_probs)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(e)
    logging.debug(f'From combined {answer_probs} {model_name} {answer_labels}')
    return answer_probs, answer_labels


def _process_text(answer):
    if isinstance(answer, dict) and 'text' in answer:
        return answer['text']
    else:
        return answer


def _process_old_sentiment(answer):
    # Input: all sentiment annotations. Output: probs
    if isinstance(answer[0], str) and isinstance(answer[1], float):
        # support old sentiment output
        curr_answer = {}
        for key in combined_classes['sentiment_classification']:
            if key == answer[0]:
                curr_answer[key] = answer[1]
            else:
                curr_answer[key] = 0.5 * (1 - answer[1])
        answer_probs = curr_answer
        return answer_probs
    else:
        logging.warning('_process_old_sentiment got file with an output that is not old-style')
        return answer


def _get_plain_annotations(annotated_utterance, model_name):
    answer_probs, answer_labels = {}, []
    try:
        annotations = annotated_utterance['annotations']
        answer = annotations[model_name]
        logging.info(f'Being processed plain annotation {answer}')
        answer = _process_text(answer)
        if type(answer) == list:
            if model_name == 'sentiment_classification':
                answer_probs = _process_old_sentiment(answer)
                answer_labels = _probs_to_labels(answer_probs)
            else:
                answer_labels = answer
                answer_probs = _labels_to_probs(answer_labels, combined_classes[model_name])
        else:
            answer_probs = answer
            answer_labels = _probs_to_labels(answer_probs)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(e)
    logging.info(f'Answer {answer_probs} {answer_labels}')
    return answer_probs, answer_labels


def print_combined(combined_output):
    combined_output = deepcopy(combined_output)
    for i in range(len(combined_output)):
        for key in combined_output[i]:
            for class_ in combined_output[i][key]:
                combined_output[i][key][class_] = round(combined_output[i][key][class_], 2)
    logging.info(f'Combined classifier output is {combined_output}')


def _get_etc_model(annotated_utterance, model_name, probs=True, default_probs={}, default_labels=[]):
    """Function to get emotion classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with emotion probablilties, if probs == True, or emotion labels if probs != True
    """
    try:
        if model_name in annotated_utterance['annotations']:
            answer_probs, answer_labels = _get_plain_annotations(annotated_utterance,
                                                                 model_name=model_name)
        else:
            answer_probs, answer_labels = _get_combined_annotations(annotated_utterance,
                                                                    model_name=model_name)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(e)
        answer_probs, answer_labels = default_probs, default_labels
    if probs:  # return probs
        return answer_probs
    else:
        return answer_labels


def get_toxic(annotated_utterance, probs=True, default_probs={}, default_labels=[]):
    """Function to get toxic classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with toxic probablilties, if probs == True, or toxic labels if probs != True
    """
    return _get_etc_model(annotated_utterance, 'toxic_classification', probs=probs,
                          default_probs=default_probs, default_labels=default_labels)


def get_sentiment(annotated_utterance, probs=True,
                  default_probs={'positive': 0, 'negative': 0, 'neutral': 1},
                  default_labels=['neutral']):
    """Function to get sentiment classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with sentiment probablilties, if probs == True, or sentiment labels if probs != True
    """
    return _get_etc_model(annotated_utterance, 'sentiment_classification', probs=probs,
                          default_probs=default_probs, default_labels=default_labels)


def get_emotions(annotated_utterance, probs=True,
                 default_probs={'anger': 0, 'fear': 0, 'joy': 0, 'love': 0,
                                'sadness': 0, 'surprise': 0, 'neutral': 1},
                 default_labels=['neutral']):
    """Function to get toxic classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with emotion probablilties, if probs == True, or toxic labels if probs != True
    """
    return _get_etc_model(annotated_utterance, 'emotion_classification', probs=probs,
                          default_probs=default_probs, default_labels=default_labels)


def get_topics(annotated_utterance, probs=False, default_probs={}, default_labels=[], which="all"):
    """Function to get topics from particular annotator or all detected.

    Args:
        annotated_utterance: dictionary with annotated utterance
        which: which topics to return.
            'all' means topics by `cobot_topics` and `cobot_dialogact_topics`,
            'cobot_topics' means topics by `cobot_topics`,
            'cobot_dialogact_topics' means topics by `cobot_dialogact_topics`.

    Returns:
        list of topics
    """
    annotations = annotated_utterance.get("annotations", {})
    cobot_topics_probs, cobot_topics_labels = {}, []
    if 'cobot_topics' in annotations:
        cobot_topics_labels = _process_text(annotations['cobot_topics'])
        cobot_topics_probs = _labels_to_probs(cobot_topics_labels, combined_classes['cobot_topics'])
    if 'combined_classification' in annotations and len(cobot_topics_labels) == 0:
        cobot_topics_probs, cobot_topics_labels = _get_combined_annotations(
            annotated_utterance, model_name='cobot_topics')
    cobot_topics_labels = _process_text(cobot_topics_labels)
    if len(cobot_topics_probs) == 0:
        cobot_topics_probs = _labels_to_probs(cobot_topics_labels,
                                              combined_classes['cobot_topics'])

    cobot_da_topics_probs, cobot_da_topics_labels = {}, []
    if "cobot_dialogact" in annotations and "topics" in annotations["cobot_dialogact"]:
        cobot_da_topics_labels = annotated_utterance["annotations"]["cobot_dialogact"]["topics"]
    elif "cobot_dialogact_topics" in annotations:
        cobot_da_topics_labels = annotated_utterance['annotations']['cobot_dialogact_topics']

    if 'combined_classification' in annotations and len(cobot_da_topics_labels) == 0:
        cobot_da_topics_probs, cobot_da_topics_labels = _get_combined_annotations(
            annotated_utterance, model_name='cobot_dialogact_topics')
    cobot_da_topics_labels = _process_text(cobot_da_topics_labels)
    if len(cobot_da_topics_probs) == 0:
        cobot_da_topics_probs = _labels_to_probs(cobot_da_topics_labels,
                                                 combined_classes['cobot_dialogact_topics'])

    if which == "all":
        answer_labels = cobot_topics_labels + cobot_da_topics_labels
        answer_probs = {**cobot_topics_probs, **cobot_da_topics_probs}
    elif which == "cobot_topics":
        answer_probs, answer_labels = cobot_topics_probs, cobot_topics_labels
    elif which == "cobot_dialogact_topics":
        answer_probs, answer_labels = cobot_da_topics_probs, cobot_da_topics_labels
    else:
        logging.exception(f'Unknown input type in get_topics: {which}')
        answer_probs, answer_labels = default_probs, default_labels
    try:
        assert len(answer_probs) > 0 and len(answer_labels) > 0, annotations
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(f'No topic annotations received - returning default')
        answer_probs, answer_labels = default_probs, default_labels
    if probs:
        return answer_probs
    else:
        return answer_labels


def get_intents(annotated_utterance, probs=False, default_probs={}, default_labels=[], which="all"):
    """Function to get intents from particular annotator or all detected.

    Args:
        annotated_utterance: dictionary with annotated utterance
        which: which intents to return.
            'all' means intents detected by `intent_catcher` and `cobot_dialogact_intents`,
            'intent_catcher' means intents detected by `intent_catcher`,
            'cobot_dialogact_intents' means intents detected by `cobot_dialogact_intents`.

    Returns:
        list of intents
    """
    annotations = annotated_utterance.get("annotations", {})
    intents = annotations.get("intent_catcher", {})
    detected_intents = [k for k, v in intents.items() if v.get("detected", 0) == 1]
    detected_intent_probs = {key: 1 for key in detected_intents}
    cobot_da_intent_probs, cobot_da_intent_labels = {}, []
    if "cobot_dialogact" in annotations and "intents" in annotations["cobot_dialogact"]:
        cobot_da_intent_labels = annotated_utterance["annotations"]["cobot_dialogact"]["intents"]
    elif 'cobot_dialogact_intents' in annotations:
        cobot_da_intent_labels = annotated_utterance['annotations']['cobot_dialogact_intents']
    if "combined_classification" in annotations and len(cobot_da_intent_labels) == 0:
        cobot_da_intent_probs, cobot_da_intent_labels = _get_combined_annotations(annotated_utterance,
                                                                                  model_name='cobot_dialogact_intents')
    cobot_da_intent_labels = _process_text(cobot_da_intent_labels)
    if len(cobot_da_intent_probs) == 0:
        cobot_da_intent_probs = _labels_to_probs(cobot_da_intent_labels,
                                                 combined_classes['cobot_dialogact_topics'])
    if which == "all":
        answer_probs = {**detected_intent_probs, **cobot_da_intent_probs}
        answer_labels = detected_intents + cobot_da_intent_labels
    elif which == "intent_catcher":
        answer_probs, answer_labels = detected_intent_probs, detected_intents
    elif which == "cobot_dialogact_intents":
        answer_probs, answer_labels = cobot_da_intent_probs, cobot_da_intent_labels
    else:
        logging.exception(f'Unknown type {which}')
        answer_probs, answer_labels = default_probs, default_labels
    try:
        assert len(answer_probs) > 0 and len(answer_labels) > 0, annotations
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(f'No intent annotations received - returning default')
        answer_probs, answer_labels = default_probs, default_labels
    if probs:
        return answer_probs
    else:
        return answer_labels
