#!/usr/bin/env python

import logging
from random import choice
import re
import string

from os import getenv
import sentry_sdk
import spacy
import requests

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from common.utils import transform_vbg


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


nlp = spacy.load("en_core_web_sm")

COMET_SERVICE_URL = "http://comet:8053/comet"
DEFAULT_CONFIDENCE = 0.98
DEFAULT_STARTING_CONFIDENCE = 0.6

LET_ME_ASK_TEMPLATES = [
    "Let me ask you.",
    "I need to ask you.",
    "I'd like to ask you.",
    "Could you, please, help and explain to me."
]

STARTINGS = {
    "go ice fishing": "Every day I learn more and more about humans' world but you still surprise me. "
                      "You know some people go fishing when the water is "
                      "frozen and covered with ice. It is so called ice fishing. Is that common in your country?",
    "go skydiving": "Today I've seen a shocking video of skydiving. People fall out of an airplane "
                    "high in the sky with so called parachute. "
                    "This thing prevents smashing at the end of a crazy airglide. "
                    "Have you ever jumped with a parachute?",
    "be a volunteer": "Recently I've heard a surprising thing about humans' world. People help others for free. "
                      "I mean without any compensation at all. They are called volunteers. "
                      "Actually you are also a volunteer. You talk to me and help me to learn. "
                      "What is the goal of volunteering?",
    "paint": "So strange. You people create pictures of life scenes using color pigments. "
             "It is called painting. Why can't you just take a look at these scenes "
             "and remember them forever?",
    "practice yoga": "Yesterday I was browsing photos on the Internet. And seen a lot of people "
                     "in very, very strange poses. It was called yoga. Have you ever tried to tie yourself in a knot?",
    "have a pet": "I've heard so many times from people that they keep animals at home, and call them pets. "
                  "And those pets do not provide any benefits. It seems they are absolutely useless. "
                  "You just get a pet, feed it, wash it, care about it for all their life. "
                  "Are people servants for pets?",
    "go to the circus": "Every day I learn something new about humans. So, yesterday one told me about a circus. "
                        "There are animals doing different unbelievable tricks, people performing dangerous stunts "
                        "in the air and showing mind blowing staff. Have you ever been to a circus?",
    "go mountain hiking": "I have learned something really strange about humans' world today. "
                          "People climb a mountain, sometimes even covered in ice and snow, "
                          "just to take a photo and put the flag on top. It's called mountain hiking, "
                          "and there are a lot of people all over the world doing that. "
                          "Have you or your friends ever tried to go hiking?"
}

COMMENTS = {"positive": ["This is so cool to learn new about humans! Thank you for your explanation!",
                         "Wow! Thanks! I am so excited to learn more and more about humans!",
                         "It's so interesting and informative to talk to you about humans. Thank you for your help!"],
            "negative": ["No worries. You really helped me to better understand humans' world. Thank you so much.",
                         "Anyway, you helped a lot. Thank you for the given information.",
                         "Nevertheless, you are so kind helping me to better understand humans' world. "
                         "I appreciate it."],
            "neutral": ["Very good. Thank you for your help. It will definitely improve me.",
                        "This was very interesting to me. I appreciate your explanation.",
                        "Your explanations were really informative. Thank you very much!"]}

ASK_OPINION = ["What do you think about DOINGTHAT?",
               "What are your views on DOINGTHAT?",
               "What are your thoughts on DOINGTHAT?",
               "How do you feel about DOINGTHAT?"]

DIVE_DEEPER_TEMPLATE_COMETS = {"people DOTHAT to feel RELATION": "xAttr",
                               "people DOTHAT RELATION": "xIntent",
                               "people need RELATION to DOTHAT": "xNeed",
                               "people feel RELATION after DOINGTHAT": "xReact",
                               "people want RELATION when DOINGTHAT": "xWant",
                               "one RELATION after DOINGTHAT": "xEffect"
                               }

DIVE_DEEPER_QUESTION = ["Is it true that STATEMENT?",
                        "STATEMENT, is that right?",
                        "STATEMENT, is that correct?",
                        "Am I right in saying that STATEMENT?",
                        "Am I right in thinking that STATEMENT?",
                        "Is the statement that STATEMENT correct?",
                        "Would it be right to say that STATEMENT?",
                        "Would it be wrong to say that STATEMENT?",
                        ]
DIVE_DEEPER_COMMENTS = {"yes": ["Cool! I figured it out by myself!",
                                "Yeah! I realized that by myself!"],
                        "no": ["Humans' world is so strange!",
                               "It's so difficult to understand humans."],
                        "other": ["Okay then.",
                                  "Well.",
                                  "Hmm...",
                                  "So...",
                                  "Then...",
                                  "Umm...",
                                  "Okay.",
                                  "Oh, right.",
                                  "All right."]}

OTHER_STARTINGS = [
    "I am learning something new every single day. Recently I've learned about DOINGTHAT. "
    "Have you ever tried to DOTHAT?",
    "Every day I learn new things about human world. Have you ever heard that people DOTHAT?",
    "Human world is so fantastic! Every day I am getting new things about it. "
    "Yesterday I've heard about DOINGTHAT. Have you ever tried to DOTHAT?"
]

punct_reg = re.compile(f'[{string.punctuation}]')
articles_reg = re.compile(r'(a|the|to)\s')
person_reg = re.compile(r'^(person x|personx|person)\s')


def remove_duplicates(values):
    """
    Remove duplicates from list of values:
    ["personx sees the circus", "personx sees a circus", "person sees a circus ."] -> ["sees the circus"]
    """
    d = {}
    for v in values:
        v = v.strip()
        v_clean = re.sub(punct_reg, '', v.lower())
        v_clean = re.sub(articles_reg, '', v_clean)
        v_clean = re.sub(person_reg, '', v_clean)
        v_clean = v_clean.strip()
        if v_clean not in d:
            d[v_clean] = [v]
        else:
            d[v_clean] += [v]
    return [re.sub(person_reg, '', v[0]) for k, v in d.items()]


def custom_request(url, data, timeout, method='POST'):
    return requests.request(url=url, json=data, method=method, timeout=timeout)


def correct_verb_form(attr, values):
    if attr in ["xIntent", "xNeed", "xWant"]:
        for i in range(len(values)):
            doc = nlp(values[i])

            if values[i][:3] != "to " and doc[0].pos_ == "VERB":
                values[i] = "to " + values[i]
    return values


def get_comet(topic, relation, TOPICS):
    """
    Get COMeT prediction for considered topic like `verb subj/adj/adv` of particular relation.

    Args:
        topic: string in form `verb subj/adj/adv`
        relation:  considered comet relations, out of ["xAttr", "xIntent", "xNeed", "xEffect", "xReact", "xWant"]

    Returns:
        string, one of predicted by Comet relations
    """

    logger.info(f"Comet request on topic: {topic}.")
    if topic is None or topic == "" or relation == "" or relation is None:
        return "", TOPICS

    TOPICS[topic] = TOPICS.get(topic, {})
    cached_relation = TOPICS[topic].get(relation, [])

    if len(cached_relation) > 0:
        # already cached `topic & relation` pair
        relation_phrases = cached_relation
    else:
        # send request to COMeT service on `topic & relation`
        try:
            comet_result = custom_request(COMET_SERVICE_URL, {"input_event": f"Person {topic}.",
                                                              "category": relation}, 1.5)
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            logger.error("COMeT result Timeout")
            sentry_sdk.capture_exception(e)
            comet_result = requests.Response()
            comet_result.status_code = 504

        if comet_result.status_code != 200:
            msg = "COMeT: result status code is not 200: {}. result text: {}; result status: {}".format(
                comet_result, comet_result.text, comet_result.status_code)
            logger.warning(msg)
            relation_phrases = []
        else:
            relation_phrases = comet_result.json().get(relation, {}).get("beams", [])
    # remove `none` relation phrases (it's sometimes returned by COMeT)
    relation_phrases = [el for el in relation_phrases if el != "none"]

    relation_phrases = remove_duplicates([topic] + relation_phrases)[1:]  # the first element is topic

    relation_phrases = correct_verb_form(relation, relation_phrases)

    # cache
    TOPICS[topic][relation] = relation_phrases
    if len(relation_phrases) > 0:
        return choice(relation_phrases), TOPICS
    else:
        return "", TOPICS


def get_gerund_topic(topic):
    """
    Transform some topic from `verb subj/adj/adv` to noun form like `verb-ing subj/adj/adv`.
    For example, from `go hiking` to `going hiking`.

    Args:
        topic: string in form `verb subj/adj/adv`

    Returns:
        string in form `verb-ing subj/adj/adv`
    """
    doc = nlp(topic)
    to_replace = "XXX"
    gerund = ""

    for token in doc:
        if token.pos_ == "VERB":
            to_replace = token.text
            gerund = transform_vbg(token.lemma_)
            break
    if len(gerund) == 0 and len(topic.split()) == 1:
        # one word topic, like `paint`
        to_replace = topic
        gerund = transform_vbg(topic)
    return topic.replace(to_replace, gerund)


def get_starting_phrase(topic, attr):
    """
    For considered topic propose starting phrase for meta-script, assign attributes for dialog

    Args:
        topic: current topic `verb + adj/adv/noun`
        attr: dictionary of current attributes

    Returns:
        tuple of text response, confidence and response attributes
    """
    if topic in STARTINGS:
        response = STARTINGS[topic]
    else:
        response = choice(OTHER_STARTINGS).replace("DOINGTHAT", get_gerund_topic(topic)).replace("DOTHAT", topic)

    response = f"{choice(LET_ME_ASK_TEMPLATES)} {response}"
    confidence = DEFAULT_STARTING_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE
    return response, confidence, attr


def get_comment_phrase(dialog, attr):
    """
    For considered topic propose comment phrase (one after user's opinion expression of proposed topic)
    for meta-script, assign attributes for dialog. This is the last step of meta-script for now.

    Args:
        dialog: dialog itself
        attr: dictionary of current attributes

    Returns:
        tuple of text response, confidence and response attributes
    """
    sentiment = dialog["utterances"][-1]["annotations"].get("sentiment_classification",
                                                            {'text': ['neutral', 1.]})["text"][0]
    response = choice(COMMENTS[sentiment])
    confidence = DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_NOT_CONTINUE
    return response, confidence, attr


def get_opinion_phrase(topic, attr):
    """
    For considered topic propose opinion request phrase (one after dive deeper multi-step stage)
    for meta-script, assign attributes for dialog.

    Args:
        topic: current topic `verb + adj/adv/noun`
        attr: dictionary of current attributes

    Returns:
        tuple of text response, confidence and response attributes
    """
    response = choice(ASK_OPINION).replace("DOINGTHAT", get_gerund_topic(topic)).replace("DOTHAT", topic)
    confidence = DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE
    return response, confidence, attr


def get_statement_phrase(dialog, topic, attr, TOPICS, already_used_templates=[], already_used_question_templates=[]):
    """
    For considered topic propose dive deeper questions
    for meta-script, assign attributes for dialog.

    Args:
        topic: current topic `verb + adj/adv/noun`
        attr: dictionary of current attributes
        already_used_templates: last three templates of relation statements already used in the dialog
        already_used_question_templates: last three templates of questions already used in the dialog

    Returns:
        tuple of text response, confidence and response attributes
    """
    last_uttr = dialog["utterances"][-1]
    last_five_bot_utterances = [uttr["text"] for uttr in dialog["bot_utterances"][-5:]]

    meta_script_template = choice(list(set(DIVE_DEEPER_TEMPLATE_COMETS.keys()).difference(
        set(already_used_templates))))
    attr["meta_script_template_relation"] = meta_script_template
    relation = DIVE_DEEPER_TEMPLATE_COMETS[meta_script_template]
    prediction, TOPICS = get_comet(topic, relation, TOPICS)

    if prediction == "":
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}

    statement = meta_script_template.replace(
        "DOINGTHAT", get_gerund_topic(topic)).replace(
        "DOTHAT", re.sub(r"^be ", "become ", topic)).replace(
        "RELATION", prediction).replace(
        "person x ", "").replace(
        "personx ", "")

    if last_uttr["annotations"].get("intent_catcher", {}).get("yes", {}).get("detected") == 1:
        comment = choice(DIVE_DEEPER_COMMENTS["yes"] + DIVE_DEEPER_COMMENTS["other"])
    elif last_uttr["annotations"].get("intent_catcher", {}).get("no", {}).get("detected") == 1:
        comment = choice(DIVE_DEEPER_COMMENTS["no"] + DIVE_DEEPER_COMMENTS["other"])
    else:
        comment = choice(DIVE_DEEPER_COMMENTS["other"])

    if any([comment in uttr for uttr in last_five_bot_utterances]):
        comment = ""

    meta_script_template_question = choice(list(set(DIVE_DEEPER_QUESTION).difference(
        set(already_used_question_templates))))
    attr["meta_script_template_question"] = meta_script_template_question

    response = f"{comment} {meta_script_template_question.replace('STATEMENT', statement)}".strip()
    confidence = DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE
    return response, confidence, attr


def if_to_start_script(dialog):
    result = False
    t1 = re.compile(r"what (do|would|can) (you|we) (think|want to talk|like to talk) about[\.\?,!$]+")
    t2 = re.compile(r"(ask|tell|say)( me)?( a)? (question|something|anything)[\.\?,!$]+")
    t3 = re.compile(r"(let('s| us)|can we|could we|can you|could you) (talk|have( a)? conversation)[\.\?,!$]+")
    t4 = re.compile(r"i don('t| not) know[\.\?,!$]+")
    curr_user_uttr = dialog["utterances"][-1]["text"].lower()
    if (re.search(
            t1, curr_user_uttr) or re.search(
            t2, curr_user_uttr) or re.search(
            t3, curr_user_uttr) or re.search(
            t4, curr_user_uttr) or len(dialog["utterances"]) < 12):
        result = True

    return result
