import re
import logging
from os import getenv
from copy import deepcopy
from random import choice

from common.custom_requests import request_triples_wikidata
import sentry_sdk

logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))

other_skills = {
    "dff_intent_responder_skill",
    "dff_program_y_dangerous_skill",
    "misheard_asr",
    "christmas_new_year_skill",
    "superbowl_skill",
    "oscar_skill",
    "valentines_day_skill",
}
scenario_skills = {
    "dff_movie_skill",
    "personal_info_skill",  # 'short_story_skill',
    "dff_book_skill",
    "dff_weather_skill",
    "emotion_skill",
    "dummy_skill_dialog",
    "meta_script_skill",
    "dff_coronavirus_skill",
    "small_talk_skill",
    "news_api_skill",
    "game_cooperative_skill",
}
retrieve_skills = {
    "dff_program_y_skill",
    "alice",
    "eliza",
    "book_tfidf_retrieval",
    "entertainment_tfidf_retrieval",
    "fashion_tfidf_retrieval",
    "movie_tfidf_retrieval",
    "music_tfidf_retrieval",
    "politics_tfidf_retrieval",
    "science_technology_tfidf_retrieval",
    "sport_tfidf_retrieval",
    "animals_tfidf_retrieval",
    "convert_reddit",
    "topicalchat_convert_retrieval",
    "dff_program_y_wide_skill",
    "knowledge_grounding_skill",
}

okay_statements = {
    "Okay.",
    "That's cool!",
    "Interesting.",
    "Sounds interesting.",
    "Sounds interesting!",
    "OK.",
    "Cool!",
    "Thanks!",
    "Okay, thanks.",
    "I'm glad you think so!",
    "Sorry, I don't have an answer for that!",
    "Let's talk about something else.",
    "As you wish.",
    "All right.",
    "Right.",
    "Anyway.",
    "Oh, okay.",
    "Oh, come on.",
    "Really?",
    "Okay. I got it.",
    "Well, okay.",
    "Well, as you wish.",
}

service_intents = {
    "lets_chat_about",
    "tell_me_more",
    "topic_switching",
    "yes",
    "opinion_request",
    "dont_understand",
    "no",
    "stupid",
    "weather_forecast_intent",
    "doing_well",
    "tell_me_a_story",
    "choose_topic",
}

high_priority_intents = {
    "dff_intent_responder_skill": {
        "cant_do",
        "exit",
        "repeat",
        "what_can_you_do",
        "what_is_your_job",
        "what_is_your_name",
        "where_are_you_from",
        "who_made_you",
        "track_object",
        "turn_around",
        "move_forward",
        "move_backward",
        "open_door",
        "move_to_point"
    },
    "dff_grounding_skill": {"what_are_you_talking_about"},
}

low_priority_intents = {"dont_understand", "what_time", "choose_topic"}

combined_classes = {
    "factoid_classification": ["is_factoid", "is_conversational"],
    "emotion_classification": ["anger", "fear", "joy", "love", "sadness", "surprise", "neutral"],
    "toxic_classification": [
        "identity_hate",
        "insult",
        "obscene",
        "severe_toxic",
        "sexual_explicit",
        "threat",
        "toxic",
        "not_toxic",
    ],
    "sentiment_classification": ["positive", "negative", "neutral"],
    "cobot_topics": [
        "Phatic",
        "Other",
        "Movies_TV",
        "Music",
        "SciTech",
        "Literature",
        "Travel_Geo",
        "Celebrities",
        "Games",
        "Pets_Animals",
        "Sports",
        "Psychology",
        "Religion",
        "Weather_Time",
        "Food_Drink",
        "Politics",
        "Sex_Profanity",
        "Art_Event",
        "Math",
        "News",
        "Entertainment",
        "Fashion",
    ],
    "cobot_dialogact_topics": [
        "Other",
        "Phatic",
        "Entertainment_Movies",
        "Entertainment_Books",
        "Entertainment_General",
        "Interactive",
        "Entertainment_Music",
        "Science_and_Technology",
        "Sports",
        "Politics",
        "Inappropriate_Content",
    ],
    "cobot_dialogact_intents": [
        "Information_DeliveryIntent",
        "General_ChatIntent",
        "Information_RequestIntent",
        "User_InstructionIntent",
        "InteractiveIntent",
        "Opinion_ExpressionIntent",
        "OtherIntent",
        "ClarificationIntent",
        "Topic_SwitchIntent",
        "Opinion_RequestIntent",
        "Multiple_GoalsIntent",
    ],
}

midas_classes = {
    "semantic_request": {
        "question": [
            "open_question_factual",
            "open_question_opinion",
            "open_question_personal",
            "yes_no_question",
            "clarifying_question",
        ],
        "command": ["command", "dev_command"],
        "opinion": ["appreciation", "opinion", "complaint", "comment"],
        "statement": ["statement"],
        "answer": ["other_answers", "pos_answer", "neg_answer"],
    },
    "functional_request": {
        "incomplete": ["abandon", "nonsense"],
        "social_convention": ["opening", "closing", "hold", "back-channeling"],
        "apology": [],
        "other": ["uncertain", "non_compliant", "correction"],
    },
}
MIDAS_SEMANTIC_LABELS = sum([intent_list for intent_list in midas_classes["semantic_request"].values()], [])
MIDAS_FUNCTIONAL_LABELS = sum([intent_list for intent_list in midas_classes["functional_request"].values()], [])


def join_words_in_or_pattern(words):
    return r"(" + r"|".join([r"\b%s\b" % word for word in words]) + r")"


def join_word_beginnings_in_or_pattern(words):
    return r"(" + r"|".join([r"\b%s" % word for word in words]) + r")"


def join_sentences_in_or_pattern(sents):
    return r"(" + r"|".join(sents) + r")"


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
                        if not activated and skop:
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
    s += "+VBG"
    # irregular cases
    s1 = re.compile(r"(?<![a-z])be\+VBG")
    s2 = re.compile(r"(?<![aouiey])([^aouiey][aouiey]([^aouieywr]))\+VBG")
    s3 = re.compile(r"ie\+VBG")
    s4 = re.compile(r"(ee)\+VBG")
    s5 = re.compile(r"e\+VBG")
    # regular case
    s6 = re.compile(r"\+VBG")

    # irregular cases
    s = re.sub(s1, "being", s)
    s = re.sub(s2, r"\1\2ing", s)
    s = re.sub(s3, r"ying", s)
    s = re.sub(s4, r"\1ing", s)
    s = re.sub(s5, r"ing", s)
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


yes_templates = re.compile(
    r"(\byes\b|\byup\b|\byep\b|\bsure\b|go ahead|\byeah\b|\bok\b|okay|^(kind of|kinda)\.?$|"
    r"^why not\.?$|^tell me\.?$|^i (agree|do|did|like|have|had|think so)\.?$)"
)


def is_yes(annotated_phrase):
    yes_detected = "yes" in get_intents(annotated_phrase, which="intent_catcher", probs=False)
    midas_yes_detected = "pos_answer" in get_intents(annotated_phrase, which="midas", probs=False)
    # TODO: intent catcher not catches 'yes thanks!'
    if yes_detected or midas_yes_detected or re.search(yes_templates, annotated_phrase.get("text", "").lower()):
        return True
    return False


no_templates = re.compile(r"(\bno\b|\bnot\b|no way|don't|no please|i disagree|^neither.?$)")
DONOTKNOW_LIKE = [r"(i )?(do not|don't) know", "you (choose|decide|pick up)", "no idea"]
DONOTKNOW_LIKE_PATTERN = re.compile(join_sentences_in_or_pattern(DONOTKNOW_LIKE), re.IGNORECASE)


def is_donot_know(annotated_phrase):
    if DONOTKNOW_LIKE_PATTERN.search(annotated_phrase.get("text", "")):
        return True
    return False


def is_no_intent(annotated_phrase):
    no_detected = "no" in get_intents(annotated_phrase, which="intent_catcher", probs=False)
    midas_no_detected = False  # "neg_answer" in get_intents(annotated_phrase, which='midas', probs=False)
    is_not_idontknow = not is_donot_know(annotated_phrase)
    if (no_detected or midas_no_detected) and is_not_idontknow:
        return True

    return False


def is_no(annotated_phrase):
    no_detected = "no" in get_intents(annotated_phrase, which="intent_catcher", probs=False)
    midas_no_detected = "neg_answer" in get_intents(annotated_phrase, which="midas", probs=False)
    # TODO: intent catcher thinks that horrible is no intent'
    user_phrase = annotated_phrase.get("text", "").lower().strip().replace(".", "")
    is_not_horrible = "horrible" != user_phrase
    no_regexp_detected = re.search(no_templates, annotated_phrase.get("text", "").lower())
    is_not_idontknow = not is_donot_know(annotated_phrase)
    _yes = is_yes(annotated_phrase)
    if is_not_horrible and (no_detected or midas_no_detected or no_regexp_detected) and is_not_idontknow and not _yes:
        return True

    return False


def is_question(text):
    return "?" in text


def substitute_nonwords(text):
    return re.sub(r"\W+", " ", text).strip()


def get_intent_name(text):
    splitter = "#+#"
    if splitter not in text:
        return None
    intent_name = text.split(splitter)[-1]
    intent_name = re.sub(r"\W", " ", intent_name.lower()).strip()
    return intent_name


OPINION_REQUEST_PATTERN = re.compile(
    r"(don't|do not|not|are not|are|do)?\s?you\s"
    r"(like|dislike|adore|hate|love|believe|consider|get|know|taste|think|"
    r"recognize|sure|understand|feel|fond of|care for|fansy|appeal|suppose|"
    r"imagine|guess)",
    re.IGNORECASE,
)
OPINION_EXPRESSION_PATTERN = re.compile(
    r"\bi (don't|do not|not|am not|'m not|am|do)?\s?"
    r"(like|dislike|adore|hate|love|believe|consider|get|know|taste|think|"
    r"recognize|sure|understand|feel|fond of|care for|fansy|appeal|suppose|"
    r"imagine|guess)",
    re.IGNORECASE,
)


def is_opinion_request(annotated_utterance):
    intents = get_intents(annotated_utterance, which="all", probs=False)
    intent_detected = any([intent in intents for intent in ["Opinion_RequestIntent", "open_question_opinion"]])
    uttr_text = annotated_utterance.get("text", "")
    if intent_detected or (OPINION_REQUEST_PATTERN.search(uttr_text) and "?" in uttr_text):
        return True
    else:
        return False


def is_opinion_expression(annotated_utterance):
    all_intents = get_intents(annotated_utterance, which="all")
    intent_detected = any([intent in all_intents for intent in ["opinion", "Opinion_ExpressionIntent"]])
    uttr_text = annotated_utterance.get("text", "")
    if intent_detected or OPINION_EXPRESSION_PATTERN.search(uttr_text):
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
                    if activated and skop["text"] in final_response and skop:
                        result.append(skop)
                    else:
                        if not activated and skop:
                            result.append(skop)
        elif "hypotheses" in uttr:
            skills_outputs = uttr["hypotheses"]

    return result


def get_not_used_template(used_templates, all_templates, any_if_no_available=True):
    """
    Choose not used template among all templates

    Args:
        used_templates: list of templates already used in the dialog
        all_templates: list of all available templates

    Returns:
        string template
    """
    available = list(set(all_templates).difference(set(used_templates)))
    if available:
        return choice(available)
    elif any_if_no_available:
        return choice(all_templates)
    else:
        return ""


def get_all_not_used_templates(used_templates, all_templates):
    """
    Return all not used template among all templates

    Args:
        used_templates: list of templates already used in the dialog
        all_templates: list of all available templates

    Returns:
        string template
    """
    available = list(set(all_templates).difference(set(used_templates)))
    return available


def _probs_to_labels(answer_probs, max_proba=True, threshold=0.5):
    answer_labels = [label for label in answer_probs if answer_probs[label] > threshold]
    if not answer_labels and max_proba:
        answer_labels = [key for key in answer_probs if answer_probs[key] == max(answer_probs.values())]
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
        annotations = annotated_utterance["annotations"]
        combined_annotations = annotations.get("combined_classification", {})
        if combined_annotations and isinstance(combined_annotations, list):
            combined_annotations = combined_annotations[0]
        if model_name in combined_annotations:
            answer_probs = combined_annotations[model_name]
        else:
            raise Exception(f"Not found Model name {model_name} in combined annotations {combined_annotations}")
        if model_name == "toxic_classification" and "factoid_classification" not in combined_annotations:
            answer_labels = _probs_to_labels(answer_probs, max_proba=False, threshold=0.5)
        else:
            answer_labels = _probs_to_labels(answer_probs, max_proba=True, threshold=0.5)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return answer_probs, answer_labels


def _process_text(answer):
    if isinstance(answer, dict) and "text" in answer:
        return answer["text"]
    else:
        return answer


def _process_old_sentiment(answer):
    # Input: all sentiment annotations. Output: probs
    if isinstance(answer[0], str) and isinstance(answer[1], float):
        # support old sentiment output
        curr_answer = {}
        for key in combined_classes["sentiment_classification"]:
            if key == answer[0]:
                curr_answer[key] = answer[1]
            else:
                curr_answer[key] = 0.5 * (1 - answer[1])
        answer_probs = curr_answer
        return answer_probs
    else:
        logger.warning("_process_old_sentiment got file with an output that is not old-style")
        return answer


def _get_plain_annotations(annotated_utterance, model_name):
    answer_probs, answer_labels = {}, []
    try:
        annotations = annotated_utterance["annotations"]
        answer = annotations[model_name]

        answer = _process_text(answer)
        if isinstance(answer, list):
            if model_name == "sentiment_classification":
                answer_probs = _process_old_sentiment(answer)
                answer_labels = _probs_to_labels(answer_probs, max_proba=True, threshold=0.5)
            else:
                answer_labels = answer
                answer_probs = _labels_to_probs(answer_labels, combined_classes[model_name])
        else:
            answer_probs = answer
            if model_name == "toxic_classification":
                # this function is only for plain annotations (when toxic_classification is a separate annotator)
                answer_labels = _probs_to_labels(answer_probs, max_proba=False, threshold=0.5)
            else:
                answer_labels = _probs_to_labels(answer_probs, max_proba=True, threshold=0.5)
    except Exception as e:
        logger.warning(e)

    return answer_probs, answer_labels


def print_combined(combined_output):
    combined_output = deepcopy(combined_output)
    for i in range(len(combined_output)):
        for key in combined_output[i]:
            for class_ in combined_output[i][key]:
                combined_output[i][key][class_] = round(combined_output[i][key][class_], 2)
    logger.info(f"Combined classifier output is {combined_output}")


def _get_etc_model(annotated_utterance, model_name, probs, default_probs, default_labels):
    """Function to get emotion classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with emotion probablilties, if probs == True, or emotion labels if probs != True
    """

    try:
        if model_name in annotated_utterance.get("annotations", {}):
            answer_probs, answer_labels = _get_plain_annotations(annotated_utterance, model_name=model_name)
        elif "combined_classification" in annotated_utterance.get("annotations", {}):
            answer_probs, answer_labels = _get_combined_annotations(annotated_utterance, model_name=model_name)
        else:
            answer_probs, answer_labels = default_probs, default_labels
    except Exception as e:
        logger.exception(e, stack_info=True)
        answer_probs, answer_labels = default_probs, default_labels
    if probs:  # return probs
        return answer_probs
    else:
        return answer_labels


def get_toxic(annotated_utterance, probs=True, default_probs=None, default_labels=None):
    """Function to get toxic classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with toxic probablilties, if probs == True, or toxic labels if probs != True
    """
    default_probs = {} if default_probs is None else default_probs
    default_labels = [] if default_labels is None else default_labels
    return _get_etc_model(
        annotated_utterance,
        "toxic_classification",
        probs=probs,
        default_probs=default_probs,
        default_labels=default_labels,
    )


def get_factoid(annotated_utterance, probs=True, default_probs=None, default_labels=None):
    """Function to get factoid classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with factoid probablilties, if probs == True, or factoid labels if probs != True
    """
    default_probs = {"is_conversational": 1} if default_probs is None else default_probs
    default_labels = ["is_conversational"] if default_labels is None else default_labels
    return _get_etc_model(
        annotated_utterance,
        "factoid_classification",
        probs=probs,
        default_probs=default_probs,
        default_labels=default_labels,
    )


def get_sentiment(annotated_utterance, probs=True, default_probs=None, default_labels=None):
    """Function to get sentiment classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with sentiment probablilties, if probs == True, or sentiment labels if probs != True
    """
    default_probs = {"positive": 0, "negative": 0, "neutral": 1} if default_probs is None else default_probs
    default_labels = ["neutral"] if default_labels is None else default_labels

    return _get_etc_model(
        annotated_utterance,
        "sentiment_classification",
        probs=probs,
        default_probs=default_probs,
        default_labels=default_labels,
    )


def get_emotions(annotated_utterance, probs=True, default_probs=None, default_labels=None):
    """Function to get emotion classifier annotations from annotated utterance.

    Args:
        annotated_utterance: dictionary with annotated utterance, or annotations
        probs: return probabilities or not
        default: default value to return. If it is None, returns empty dict/list depending on probs argument
    Returns:
        dictionary with emotion probablilties, if probs == True, or emotion labels if probs != True
    """
    default_probs = (
        {"anger": 0, "fear": 0, "joy": 0, "love": 0, "sadness": 0, "surprise": 0, "neutral": 1}
        if default_probs is None
        else default_probs
    )
    default_labels = ["neutral"] if default_labels is None else default_labels

    return _get_etc_model(
        annotated_utterance,
        "emotion_classification",
        probs=probs,
        default_probs=default_probs,
        default_labels=default_labels,
    )


def get_topics(annotated_utterance, probs=False, default_probs=None, default_labels=None, which="all"):
    """Function to get topics from particular annotator or all detected.

    Args:
        annotated_utterance: dictionary with annotated utterance
        probs: if False we return labels, otherwise we return probs
        default_probs: default probabilities to return
        default_labels: default labels to return
        which: which topics to return.
            'all' means topics by `cobot_topics` and `cobot_dialogact_topics`,
            'cobot_topics' means topics by `cobot_topics`,
            'cobot_dialogact_topics' means topics by `cobot_dialogact_topics`.

    Returns:
        list of topic labels, if probs == False,
        dictionary where all keys are topic labels and values are probabilities, if probs == True
    """
    default_probs = {} if default_probs is None else default_probs
    default_labels = [] if default_labels is None else default_labels
    annotations = annotated_utterance.get("annotations", {})
    cobot_topics_probs, cobot_topics_labels = {}, []
    if "cobot_topics" in annotations:
        cobot_topics_labels = _process_text(annotations.get("cobot_topics", {}))
        cobot_topics_probs = _labels_to_probs(cobot_topics_labels, combined_classes.get("cobot_topics", {}))
    if "combined_classification" in annotations and not cobot_topics_labels:
        cobot_topics_probs, cobot_topics_labels = _get_combined_annotations(
            annotated_utterance, model_name="cobot_topics"
        )
    cobot_topics_labels = _process_text(cobot_topics_labels)
    if not cobot_topics_probs:
        cobot_topics_probs = _labels_to_probs(cobot_topics_labels, combined_classes.get("cobot_topics", {}))

    cobot_da_topics_probs, cobot_da_topics_labels = {}, []
    if "cobot_dialogact" in annotations and "topics" in annotations["cobot_dialogact"]:
        cobot_da_topics_labels = annotated_utterance["annotations"]["cobot_dialogact"]["topics"]
    elif "cobot_dialogact_topics" in annotations:
        cobot_da_topics_labels = annotated_utterance["annotations"]["cobot_dialogact_topics"]

    if "combined_classification" in annotations and not cobot_da_topics_labels:
        cobot_da_topics_probs, cobot_da_topics_labels = _get_combined_annotations(
            annotated_utterance, model_name="cobot_dialogact_topics"
        )
    cobot_da_topics_labels = _process_text(cobot_da_topics_labels)
    if not cobot_da_topics_probs:
        cobot_da_topics_probs = _labels_to_probs(cobot_da_topics_labels, combined_classes["cobot_dialogact_topics"])

    if which == "all":
        answer_labels = cobot_topics_labels + cobot_da_topics_labels
        answer_probs = {**cobot_topics_probs, **cobot_da_topics_probs}
    elif which == "cobot_topics":
        answer_probs, answer_labels = cobot_topics_probs, cobot_topics_labels
    elif which == "cobot_dialogact_topics":
        answer_probs, answer_labels = cobot_da_topics_probs, cobot_da_topics_labels
    else:
        logger.exception(f"Unknown input type in get_topics: {which}")
        answer_probs, answer_labels = default_probs, default_labels

    if probs:
        return answer_probs
    else:
        return answer_labels


def get_intents(annotated_utterance, probs=False, default_probs=None, default_labels=None, which="all"):
    """Function to get intents from particular annotator or all detected.

    Args:
        annotated_utterance: dictionary with annotated utterance
        probs: if False we return labels, otherwise we return probs
        default_probs: default probabilities to return
        default_labels: default labels to return
        which: which intents to return:
            'all' means intents detected by `intent_catcher`,
            `cobot_dialogact_intents` and  `midas_classification`.
            'intent_catcher' means intents detected by `intent_catcher`.
            'cobot_dialogact_intents' means intents detected by `cobot_dialogact_intents`.
            'midas' means intents detected by `midas_classification`.
    Returns:
        list of intent labels, if probs == False,
        dictionary where all keys are intent labels and values are probabilities, if probs == True
    """
    default_probs = {} if default_probs is None else default_probs
    default_labels = [] if default_labels is None else default_labels
    annotations = annotated_utterance.get("annotations", {})
    intents = annotations.get("intent_catcher", {})
    detected_intents = [k for k, v in intents.items() if v.get("detected", 0) == 1]
    detected_intent_probs = {key: 1 for key in detected_intents}

    midas_intent_probs = annotations.get("midas_classification", {})
    if isinstance(midas_intent_probs, dict) and midas_intent_probs:
        semantic_midas_probs = {k: v for k, v in midas_intent_probs.items() if k in MIDAS_SEMANTIC_LABELS}
        functional_midas_probs = {k: v for k, v in midas_intent_probs.items() if k in MIDAS_FUNCTIONAL_LABELS}
        if semantic_midas_probs:
            max_midas_semantic_prob = max(semantic_midas_probs.values())
        else:
            max_midas_semantic_prob = 0.0
        if functional_midas_probs:
            max_midas_functional_prob = max(functional_midas_probs.values())
        else:
            max_midas_functional_prob = 0.0

        midas_semantic_intent_labels = [k for k, v in semantic_midas_probs.items() if v == max_midas_semantic_prob]
        midas_functional_intent_labels = [
            k for k, v in functional_midas_probs.items() if v == max_midas_functional_prob
        ]
        midas_intent_labels = midas_semantic_intent_labels + midas_functional_intent_labels
    elif isinstance(midas_intent_probs, list):
        if midas_intent_probs:
            # now it's a list of dictionaries. length of list is n sentences
            midas_intent_labels = []
            for midas_sent_probs in midas_intent_probs:
                max_midas_sent_prob = max(midas_sent_probs.values())
                midas_intent_labels += [k for k, v in midas_sent_probs.items() if v == max_midas_sent_prob]
            _midas_intent_probs = deepcopy(midas_intent_probs)
            midas_intent_probs = {}
            class_names = list(set(sum([list(resp.keys()) for resp in _midas_intent_probs], [])))
            for class_name in class_names:
                max_proba = max([resp.get(class_name, 0.0) for resp in _midas_intent_probs])
                midas_intent_probs[class_name] = max_proba
        else:
            midas_intent_probs = {}
            midas_intent_labels = []
    else:
        midas_intent_labels = []
    cobot_da_intent_probs, cobot_da_intent_labels = {}, []

    if "cobot_dialogact" in annotations and "intents" in annotations["cobot_dialogact"]:
        cobot_da_intent_labels = annotated_utterance["annotations"]["cobot_dialogact"]["intents"]
    elif "cobot_dialogact_intents" in annotations:
        cobot_da_intent_labels = annotated_utterance["annotations"]["cobot_dialogact_intents"]

    if "combined_classification" in annotations and not cobot_da_intent_labels:
        cobot_da_intent_probs, cobot_da_intent_labels = _get_combined_annotations(
            annotated_utterance, model_name="cobot_dialogact_intents"
        )

    cobot_da_intent_labels = _process_text(cobot_da_intent_labels)
    if not cobot_da_intent_probs:
        cobot_da_intent_probs = _labels_to_probs(cobot_da_intent_labels, combined_classes["cobot_dialogact_intents"])

    if which == "all":
        answer_probs = {**detected_intent_probs, **cobot_da_intent_probs, **midas_intent_probs}
        answer_labels = detected_intents + cobot_da_intent_labels + midas_intent_labels
    elif which == "intent_catcher":
        answer_probs, answer_labels = detected_intent_probs, detected_intents
    elif which == "cobot_dialogact_intents":
        answer_probs, answer_labels = cobot_da_intent_probs, cobot_da_intent_labels
    elif which == "midas":
        answer_probs, answer_labels = midas_intent_probs, midas_intent_labels
    else:
        logger.warning(f"Unknown type in get_intents {which}")
        answer_probs, answer_labels = default_probs, default_labels

    if probs:
        return answer_probs
    else:
        return answer_labels


COBOT_ENTITIES_SKIP_LABELS = ["anaphor"]


def get_entities(annotated_utterance, only_named=False, with_labels=False, return_lemmas=False):
    entities = []
    if not only_named:
        if "entity_detection" in annotated_utterance.get("annotations", {}):
            labelled_entities = annotated_utterance["annotations"]["entity_detection"].get("labelled_entities", [])
            # skip some labels
            entities = [ent for ent in labelled_entities if ent["label"] not in COBOT_ENTITIES_SKIP_LABELS]
            if not with_labels:
                entities = [ent["text"] for ent in entities]
        elif "spacy_nounphrases" in annotated_utterance.get("annotations", {}):
            entities = annotated_utterance.get("annotations", {}).get("spacy_nounphrases", [])
            if with_labels:
                # actually there are no labels for cobot nounphrases
                # so, let's make it as for cobot_entities format
                entities = [{"text": ent, "label": "misc"} for ent in entities]
        if len(entities) == 0 and "spacy_annotator" in annotated_utterance.get("annotations", {}):
            words = annotated_utterance["annotations"]["spacy_annotator"]
            for word in words:
                if word.get("pos_", "") == "NOUN":
                    entities += [{"text": word["lemma_"] if return_lemmas else word["text"], "label": "misc"}]
            if not with_labels:
                entities = [ent["text"] for ent in entities]
    else:
        # `ner` contains list of lists of dicts. the length of the list is n-sentences
        # each entity is {"confidence": 1, "end_pos": 1, "start_pos": 0, "text": "unicorns", "type": "ORG"}
        entities = annotated_utterance.get("annotations", {}).get("ner", [])
        entities = sum(entities, [])  # flatten list, now it's a list of dicts-entities
        if not with_labels:
            entities = [ent["text"] for ent in entities]
    return entities if entities is not None else []


def get_named_persons(annotated_utterance):
    named_entities = get_entities(annotated_utterance, only_named=True, with_labels=True)
    all_entities = get_entities(annotated_utterance, only_named=False, with_labels=True)

    named_persons = []
    if "cobot_entities" in annotated_utterance["annotations"]:
        for ent in all_entities:
            if ent["label"] == "person":
                named_persons.append(ent["text"])
    if "ner" in annotated_utterance["annotations"]:
        for ent in named_entities:
            if ent["type"] == "PER":
                named_persons.append(ent["text"])

    named_persons = list(set(named_persons))

    return named_persons


def get_named_locations(annotated_utterance):
    named_entities = get_entities(annotated_utterance, only_named=True, with_labels=True)
    all_entities = get_entities(annotated_utterance, only_named=False, with_labels=True)

    named_locations = []
    if "cobot_entities" in annotated_utterance["annotations"]:
        for ent in all_entities:
            if ent["label"] == "location":
                named_locations.append(ent["text"])
    if len(named_locations) == 0 and "ner" in annotated_utterance["annotations"]:
        for ent in named_entities:
            if ent["type"] == "LOC" and ent["text"] != "alexa":
                _is_part_of_other_entity = False
                for cobot_ent in all_entities:
                    if ent["text"] in cobot_ent["text"] and cobot_ent["label"] != "location":
                        _is_part_of_other_entity = True
                if not _is_part_of_other_entity:
                    named_locations.append(ent["text"])

    named_locations = list(set(named_locations))
    if re.search(r"\bjapan\b", annotated_utterance["text"], re.IGNORECASE) and "japan" not in named_locations:
        # NER does not catch this country at all!
        named_locations.append("japan")

    return named_locations


def get_raw_entity_names_from_annotations(annotations):
    """

    Args:
        annotated_utterance: annotated utterance

    Returns:
        Wikidata entities we received from annotations
    """
    raw_el_output = annotations.get("entity_linking", [{}])
    entities = []
    try:
        if raw_el_output:
            if isinstance(raw_el_output[0], dict):
                entities = raw_el_output[0].get("entity_ids", [])
            if isinstance(raw_el_output[0], list):
                entities = raw_el_output[0][0]
    except Exception as e:
        error_message = f"Wrong entity linking output format {raw_el_output} : {e}"
        sentry_sdk.capture_exception(e)
        logger.exception(error_message)
    return entities


def get_entity_names_from_annotations(annotated_utterance, stopwords=None, default_entities=None):
    """

    Args:
        annotated_utterance: annotated utterance
        stopwords_file: name of file with stopwords

    Returns:
        Names of named entities we received from annotations
    """
    default_entities = [] if default_entities is None else default_entities
    stopwords = stopwords if stopwords else []
    full_text = annotated_utterance.get("text", "").lower()
    named_entities = [full_text] if full_text in default_entities else []
    annotations = annotated_utterance.get("annotations", {})
    for tmp in annotations.get("ner", []):
        if tmp and "text" in tmp[0]:
            named_entities.append(tmp[0]["text"])
    for nounphrase in annotations.get("spacy_nounphrases", []):
        named_entities.append(nounphrase)
    for wikiparser_dict in annotations.get("wiki_parser", [{}]):
        for wiki_entity_name in wikiparser_dict:
            named_entities.append(wiki_entity_name)
    named_entities = [
        entity
        for entity in named_entities
        if any([len(ent_word) >= 5 or ent_word not in stopwords for ent_word in entity.split(" ")])
    ]
    named_entities = list(set(named_entities))
    # remove entities which are is either too short or stopword
    return named_entities


def entity_to_label(entity):
    """

    Args:
        entity: Wikidata entity for which we need to receive the label
        If should be string, with first letter Q and other from 0 to 9, like Q5321

    Returns:

        label: label from this entity.
        If entity is in wrong format we assume that it is already label but give exception

    """
    logger.debug(f"Calling entity_to_label for {entity}")
    no_entity = not entity
    wrong_entity_type = not isinstance(entity, str)
    wrong_entity_format = entity and (entity[0] != "Q" or any([j not in "0123456789" for j in entity[1:]]))
    if no_entity or wrong_entity_type or wrong_entity_format:
        warning_text = f"Wrong entity format. We assume {entity} to be label but check the code"
        sentry_sdk.capture_exception(Exception(warning_text))
        logger.exception(warning_text)
        return entity
    label = ""
    labels = request_triples_wikidata("find_label", [(entity, "")])
    try:
        sep = '"'
        if sep in labels[0]:
            label = labels[0].split('"')[1]
        else:
            label = labels[0]
        logger.debug(f"Answer {label}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(Exception(e, "Exception in conversion of labels {labels}"))
    return label


def get_types_from_annotations(annotations, types, tocheck_relation="occupation"):
    """

    Args:
        annotations: annotations of utterance
        types: types from which we need to find one
        or ( if exclude_types is True) to find type not included in the list, if it is the entity of given type
        tocheck_relation: relation we want to check
        exclude_types: if False we look for matching types, otherwise we look for excluding types

    Returns:
        name of entity, name of type found, raw name of type found
    """
    wp_annotations = annotations.get("wiki_parser", {})
    if isinstance(wp_annotations, list) and wp_annotations:  # support 2 different formats
        wp_annotations = wp_annotations[0]
    try:
        topic_entities = wp_annotations.get("topic_skill_entities_info", {})
        for entity in topic_entities:
            for relation in topic_entities[entity]:
                if relation == tocheck_relation:
                    type_to_typename = {j[0]: j[1] for j in topic_entities[entity][relation]}
                    found_types = type_to_typename.keys()
                    matching_types = [type_to_typename[k] for k in set(found_types) & set(types)]
                    mismatching_types = [type_to_typename[k] for k in found_types if k not in types]
                    if matching_types:
                        return entity, matching_types, mismatching_types
            logger.warning("Relation to check not found")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(Exception(e, f"Exception in processing wp annotations {wp_annotations}"))
    return None, None, None


ANYTHING_EXCEPT_OF_LETTERS_AND_SPACE_COMPILED = re.compile(r"[^a-zA-Z ]")
ANYTHING_EXCEPT_OF_LETTERS_SPACE_AND_PUNCT_COMPILED = re.compile(r"[^a-zA-Z\,\.\?\!\- ]")
MULTI_SPACE_COMPILED = re.compile(r"\s+")


def clean_entities(entities):
    entities = [entity.lower() for entity in entities]
    entities = [re.sub(ANYTHING_EXCEPT_OF_LETTERS_AND_SPACE_COMPILED, " ", entity) for entity in entities]
    entities = [re.sub(MULTI_SPACE_COMPILED, " ", entity).strip() for entity in entities]
    entities = [entity.split() for entity in entities]  # now it's a list of lists of strings
    entities = sum(entities, [])  # flatten list
    return entities


def get_common_tokens_in_lists_of_strings(list_of_strings_0, list_of_strings_1):
    """
    Clean strings removing anything except of letters and spaces, split every string to tokens by spaces,
    find common tokens for two lists of strings.
    """
    list_of_strings_0 = deepcopy(list_of_strings_0)
    list_of_strings_1 = deepcopy(list_of_strings_1)

    list_of_strings_0 = clean_entities(list_of_strings_0)
    list_of_strings_1 = clean_entities(list_of_strings_1)

    common_substrings = list(set(list_of_strings_0).intersection(set(list_of_strings_1)))

    return common_substrings


SYMBOLS_EXCEPT_LETTERS_AND_DIGITS = re.compile(r"[^a-zA-Zа-яА-ЯёЁ0-9\-_ ]")
DOUBLE_SPACES = re.compile(r"\s+")


def replace_symbols_except_letters_and_digits(s):
    s = SYMBOLS_EXCEPT_LETTERS_AND_DIGITS.sub(" ", s)
    s = DOUBLE_SPACES.sub(" ", s).strip()
    return s


def remove_punctuation_from_dict_keys(element):
    if isinstance(element, dict):
        new_element = {}
        for dict_key, value in element.items():
            if isinstance(value, dict) or isinstance(value, list):
                new_value = remove_punctuation_from_dict_keys(value)
                new_element[replace_symbols_except_letters_and_digits(dict_key)] = deepcopy(new_value)
            else:
                new_element[replace_symbols_except_letters_and_digits(dict_key)] = deepcopy(value)
        return new_element
    elif isinstance(element, list):
        new_element = []
        for sub_element in element:
            if isinstance(sub_element, dict) or isinstance(sub_element, list):
                new_sub_element = remove_punctuation_from_dict_keys(sub_element)
                new_element += [new_sub_element]
            else:
                new_element += [sub_element]
        return new_element
    else:
        return element


PERSONAL_PRONOUNS = re.compile(
    r"\b(i|you|he|she|it|we|they|me|my|him|her|us|them|its|mine|your|yours|his|hers|ours|theirs|myself|yourself|himself"
    r"|herself|itself|ourselves|themselves|their)\b",
    re.IGNORECASE,
)


def find_first_complete_sentence(sentences):
    """Find first sentence without any personal pronouns."""
    for sent in sentences:
        if PERSONAL_PRONOUNS.search(sent):
            continue
        else:
            return sent
    return None


def is_toxic_or_badlisted_utterance(annotated_utterance):
    toxic_result = get_toxic(annotated_utterance, probs=False)
    toxic_result = [] if "not_toxic" in toxic_result else toxic_result
    # now toxic_result is empty if not toxic utterance
    toxic_result = True if len(toxic_result) > 0 else False
    default_badlist = {"bad_words": False}
    badlist_result = annotated_utterance.get("annotations", {}).get("badlisted_words", default_badlist)

    return toxic_result or any([badlist_result.get(bad, False) for bad in ["bad_words", "inappropriate", "profanity"]])


FACTOID_PATTERNS = re.compile(
    r"^(do you know |((can |could )you )tell me )?(please )?"
    r"((what|who|which|where) (is|are|was|were)\b|how to\b|when)",
    re.IGNORECASE,
)
COUNTER_FACTOID_PATTERNS = re.compile(r"^(what|who|which|where) (is|are|was|were)( that|[\.\?]$)\b", re.IGNORECASE)


def is_special_factoid_question(annotated_utterance):
    uttr_text = annotated_utterance.get("text", "")
    found = FACTOID_PATTERNS.search(uttr_text)
    if found and not COUNTER_FACTOID_PATTERNS.search(uttr_text):
        # remove first question like part
        rest_string = uttr_text[uttr_text.find(found[0]) + len(found[0]) :].strip()
        if PERSONAL_PRONOUNS.search(rest_string):
            # if any personal pronouns - not our case
            return False
        return True
    return False


FACTS_EXTRA_WORDS = re.compile(
    r"(this might answer your question[:\,]? "
    r"|(according to|from) (wikipedia|wikihow)[:\,]? "
    r"|here's (something|what) I found (from|on) [a-zA-Z0-9\-\.]+:"
    r"|here's a fact about [a-zA-Z0-9\- \,]+\.)",
    re.IGNORECASE,
)


def get_dialog_breakdown_annotations(annotated_utterance):
    breakdown = annotated_utterance.get("annotations", {}).get("dialog_breakdown", {}).get("breakdown", 0.0) > 0.5
    return breakdown
