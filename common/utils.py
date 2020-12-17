import re
from random import choice

from common.universal_templates import join_sentences_in_or_pattern, DONOTKNOW_LIKE


other_skills = {'intent_responder', 'program_y_dangerous', 'misheard_asr', 'christmas_new_year_skill',
                'superbowl_skill', 'oscar_skill', 'valentines_day_skill'}
scenario_skills = {'movie_skill', 'personal_info_skill', 'short_story_skill',
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
                   'no', 'stupid', 'weather_forecast_intent', 'doing_well', 'tell_me_a_story'}
low_priority_intents = {'dont_understand'}


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
                    if activated and skop["text"] in final_response and uttr["active_skill"] == skill_name and \
                            len(skop) > 0:
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


def check_about_death(last_utterance):
    if type(last_utterance) == str:
        last_utterance = {'text': last_utterance}
    return any([j in last_utterance['text'] for j in ['death', ' die', ' dying', 'mortality']])


def quarantine_end(last_utterance):
    if type(last_utterance) == str:
        last_utterance = {'text': last_utterance}
    return 'quarantine' in last_utterance['text'] and any([j in last_utterance['text'] for j in ['end', 'over']])


def about_virus(annotated_phrase):
    if type(annotated_phrase) == str:
        annotated_phrase = {'text': annotated_phrase}
    return any([j in annotated_phrase['text'].lower() for j in ['virus', 'covid', ' ill ', 'infect',
                                                                'code nineteen', 'corona', 'corana', 'corono',
                                                                'colonel', 'chrono ', 'corvette',
                                                                'kroner', 'karuna', 'toronow']])


yes_templates = re.compile(r"(\byes\b|\byup\b|\byep\b|\bsure\b|go ahead|\byeah\b|\bok\b|okay|"
                           r"^why not\.?$|^tell me\.?$|^i agree\.?$|^i think so\.?$)")


def is_yes(annotated_phrase):
    yes_detected = annotated_phrase['annotations'].get('intent_catcher', {}).get('yes', {}).get('detected') == 1
    # TODO: intent catcher not catches 'yes thanks!'
    return yes_detected or re.search(yes_templates, annotated_phrase["text"].lower())


no_templates = re.compile(r"(\bno\b|\bnot\b|no way|don't|no please|i disagree)")


def is_no(annotated_phrase):
    no_detected = annotated_phrase['annotations'].get('intent_catcher', {}).get('no', {}).get('detected') == 1
    # TODO: intent catcher thinks that horrible is no intent'
    user_phrase = annotated_phrase['text'].lower().strip().replace('.', '')
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
    intents = []  # annotations.get("cobot_dialogact_intents", {}).get("text", {})
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
