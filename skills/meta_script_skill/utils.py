#!/usr/bin/env python

import logging
from random import choice, random
import re
import string
import json
from os import getenv
import pathlib

import sentry_sdk
import spacy
import requests
from spacy.symbols import nsubj, VERB, xcomp, NOUN, ADP, dobj
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO
from common.utils import transform_vbg, get_skill_outputs_from_dialog, is_yes, is_no, get_sentiment

try:
    import constants as meta_script_skill_constants
except ModuleNotFoundError:
    import meta_script_skill.constants as meta_script_skill_constants


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


nlp = spacy.load("en_core_web_sm")

WORK_DIR = pathlib.Path(__file__).parent

# phrases appeared more than 500 times
# phrases are like `verb + noun` or `verb + prep + noun` WITHOUT articles
TOP_FREQUENT_VERB_NOUN_PHRASES = json.load((WORK_DIR / "topics_counter_10.json").open())

# for 200 -> 933 bigrams, for 300 -> 556 bigrams, for 500 -> 273 bigrams to ignore
TOP_FREQUENT_BIGRAMS_TO_IGNORE = [
    bigram for bigram in TOP_FREQUENT_VERB_NOUN_PHRASES if TOP_FREQUENT_VERB_NOUN_PHRASES[bigram] >= 200
]
# they are already sorted in decreasing order
TOP_FREQUENT_BIGRAMS_TO_FIND_VERB = {
    bigram: TOP_FREQUENT_VERB_NOUN_PHRASES[bigram]
    for bigram in TOP_FREQUENT_VERB_NOUN_PHRASES
    if TOP_FREQUENT_VERB_NOUN_PHRASES[bigram] < 200
}
TOP_1k_FREQUENT_WORDS = (WORK_DIR / "common/google-10000-english-no-swears.txt").open().read().splitlines()[:1000]
TOP_100_FREQUENT_WORDS = set(TOP_1k_FREQUENT_WORDS[:100])
TOP_1k_FREQUENT_WORDS = set(TOP_1k_FREQUENT_WORDS)

WIKI_DESCRIPTIONS = json.load((WORK_DIR / "wiki_topics_descriptions_one_sent.json").open())
list_of_hobbies = list(WIKI_DESCRIPTIONS.keys())

nltk_sentiment_classifier = SentimentIntensityAnalyzer()


def get_nltk_sentiment(text):
    result = nltk_sentiment_classifier.polarity_scores(text)
    if result.get("neg", 0.0) >= 0.05:
        return "negative"
    elif result.get("pos", 0.0) >= 0.5:
        return "positive"
    else:
        return "neutral"


def get_verb_topic(nounphrased_topic):
    doc = nlp(nounphrased_topic)
    if len(doc) == 1:
        for token in doc:
            if token.pos == VERB:
                return token.lemma_
    return f"do {nounphrased_topic}"


for hobby in list_of_hobbies:
    verb_hobby = get_verb_topic(hobby)
    WIKI_DESCRIPTIONS[verb_hobby] = WIKI_DESCRIPTIONS.pop(hobby)

punct_reg = re.compile(f"[{string.punctuation}]")
articles_reg = re.compile(r"(\ba\b|\bthe\b|\bto\b)\s")
person_reg = re.compile(r"(\bperson x\b|\bpersonx\b|\bperson\b)")


def is_custom_topic(topic):
    return not (topic in meta_script_skill_constants.STARTINGS or topic in WIKI_DESCRIPTIONS)


def is_wiki_topic(topic):
    return topic in WIKI_DESCRIPTIONS


def is_predefined_topic(topic):
    return topic in meta_script_skill_constants.STARTINGS


def remove_duplicates(values):
    """
    Remove duplicates from list of values:
    ["personx sees the circus", "personx sees a circus", "person sees a circus ."] -> ["sees the circus"]
    """
    d = {}
    for v in values:
        v = v.strip()
        v_clean = re.sub(punct_reg, "", v.lower())
        v_clean = re.sub(articles_reg, "", v_clean)
        v_clean = re.sub(person_reg, "", v_clean)
        v_clean = v_clean.strip()
        if v_clean not in d:
            d[v_clean] = [v]
        else:
            if v_clean.split()[0] not in ["feel", "need", "want"]:
                d[v_clean] += [v]

    return [re.sub(person_reg, "", v[0]) for k, v in d.items()]


def remove_all_phrases_containing_word(topic, phrases):
    cleaned_phrases = []
    doc = nlp(topic)

    for phrase in phrases:
        not_included = True
        for token in doc:
            if (
                len(token.lemma_) > 2
                and token.lemma_ not in TOP_100_FREQUENT_WORDS
                and (
                    re.search(r"\b%s" % token.lemma_, phrase)
                    or (token.text[-1] == "y" and re.search(r"\b%s" % token.text[:-1], phrase))
                )
            ):
                not_included = False
        if not_included:
            cleaned_phrases.append(phrase)
    return cleaned_phrases


def custom_request(url, data, timeout, method="POST"):
    return requests.request(url=url, json=data, method=method, timeout=timeout)


def correct_verb_form(attr, values):
    """
    Comet return "xEffect" - "does/will do something"
                 "oEffect" - "hopes they do something" / "they do something"
                 "xIntent", "xNeed", "xWant", "oWant" - "do something" / "to do something"
    Convert these phrases to "to do something".

    Args:
        attr: relation attribute for comet
        values: list of returned by comet values

    Returns:
        list of relation phrases in form "to do something"
        for ["xIntent", "xNeed", "xWant", "oWant", "CapableOf", "CausesDesire",
             "Desires", "HasFirstSubevent", "HasLastSubevent", "HasPainCharacter", "HasPainIntensity",
             "HasPrerequisite", "HasSubevent", "MotivatedByGoal", "NotCapableOf", "NotDesires", "ReceivesAction"]
    """
    if attr in [
        "xIntent",
        "xNeed",
        "xWant",
        "oWant",
        "CapableOf",
        "CausesDesire",
        "DesireOf",
        "Desires",
        "HasFirstSubevent",
        "HasLastSubevent",
        "HasPainCharacter",
        "HasPainIntensity",
        "HasPrerequisite",
        "HasSubevent",
        "MotivatedByGoal",
        "NotCapableOf",
        "NotDesires",
        "ReceivesAction",
    ]:
        for i in range(len(values)):
            if values[i][:4] == "you ":
                values[i] = values[i][4:]
            if values[i][:3] == "it ":
                values[i] = values[i][3:]

            doc = nlp(values[i])
            if values[i][:3] != "to " and doc[0].pos == VERB:
                values[i] = f"to {values[i]}"

    if attr in ["Causes", "DesireOf"]:
        for i in range(len(values)):
            if values[i][:4] == "you ":
                values[i] = get_gerund_topic(values[i][4:])
            elif values[i][:3] == "it ":
                values[i] = get_gerund_topic(values[i][3:])
            elif values[i][:7] == "person ":
                values[i] = get_gerund_topic(values[i][3:])

            if values[i][:3] == "to ":
                values[i] = values[i][3:]

            doc = nlp(values[i])
            if doc[0].pos == VERB:
                values[i] = get_gerund_topic(values[i])

    if attr in ["xEffect", "oEffect"]:
        for i in range(len(values)):
            if values[i][:6] == "hopes ":
                values[i] = values[i][6:]
            if values[i][:5] == "they ":
                values[i] = values[i][5:]
            if values[i][:5] == "will ":
                values[i] = values[i][5:]

            doc = nlp(values[i])
            if doc[0].pos == VERB:
                # convert does something to do something
                if len(doc) == 1:
                    values[i] = doc[0].lemma_
                else:
                    values[i] = doc[0].lemma_ + values[i][values[i].find(" ") :]
            if values[i][:3] != "to " and doc[0].pos == VERB:
                values[i] = "to " + values[i]
    return values


def get_comet_atomic(topic, relation, TOPICS=None):
    """
    Get COMeT prediction for considered topic like `verb subj/adj/adv` of particular relation.

    Args:
        topic: string in form `subj verb subj/adj/adv`
        relation:  considered comet relations, out of ["xAttr", "xIntent", "xNeed", "xEffect", "xReact", "xWant"]

    Returns:
        string, one of predicted by Comet relations
    """

    TOPICS = {} if TOPICS is None else TOPICS
    logger.info(f"Comet Atomic request on topic: {topic}.")
    if topic is None or topic == "" or relation == "" or relation is None or get_nltk_sentiment(topic) == "negative":
        return ""

    predefined_relation = TOPICS.get(topic, {}).get(relation, [])

    if len(predefined_relation) > 0:
        # already predefined `topic & relation` pair
        relation_phrases = predefined_relation
    else:
        # send request to COMeT service on `topic & relation`
        try:
            comet_result = custom_request(
                meta_script_skill_constants.COMET_ATOMIC_SERVICE_URL,
                {"input": f"{topic}", "category": relation},
                timeout=1.0,
            )
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            logger.error("COMeT Atomic result Timeout")
            sentry_sdk.capture_exception(e)
            comet_result = requests.Response()
            comet_result.status_code = 504

        if comet_result.status_code != 200:
            msg = "COMeT Atomic: result status code is not 200: {}. result text: {}; result status: {}".format(
                comet_result, comet_result.text, comet_result.status_code
            )
            logger.warning(msg)
            relation_phrases = []
        else:
            relation_phrases = comet_result.json().get(relation, {}).get("beams", [])
    # remove `none` relation phrases (it's sometimes returned by COMeT)
    logger.info(f"Before cleaning got relation phrases from COMeT Atomic: {relation_phrases}")
    relation_phrases = [el for el in relation_phrases if el != "none"]

    relation_phrases = remove_duplicates([topic] + relation_phrases)[1:]  # the first element is topic
    logger.info(f"After removing duplicates relation phrases from COMeT Atomic: {relation_phrases}")
    relation_phrases = remove_all_phrases_containing_word(topic, relation_phrases)
    logger.info(
        f"After removing all phrases containing topic words " f"relation phrases from COMeT Atomic: {relation_phrases}"
    )
    # check of sentiment for relation and drop it, if negative
    relation_phrases = [ph for ph in relation_phrases if len(ph) > 0 and get_nltk_sentiment(ph) != "negative"]

    relation_phrases = correct_verb_form(relation, relation_phrases)
    logger.info(f"After correcting verb form relation phrases from COMeT Atomic: {relation_phrases}")

    if len(relation_phrases) > 0:
        return choice(relation_phrases)
    else:
        return ""


def get_comet_conceptnet(topic, relation, return_all=False, return_not_filtered=False):
    """
    Get COMeT ConceptNet prediction for considered topic like `verb subj/adj/adv` of particular relation.

    Args:
        topic: string in form of nounphrase
        relation:  considered comet relations, out of ["xAttr", "xIntent", "xNeed", "xEffect", "xReact", "xWant"]

    Returns:
        string, one of predicted by Comet relations
    """

    logger.info(f"Comet ConceptNet request on topic: {topic}.")
    if topic is None or topic == "" or relation == "" or relation is None or get_nltk_sentiment(topic) == "negative":
        return ""

    # send request to COMeT ConceptNet service on `topic & relation`
    try:
        comet_result = custom_request(
            meta_script_skill_constants.COMET_CONCEPTNET_SERVICE_URL,
            {"input": f"{topic}.", "category": relation},
            timeout=1.0,
        )
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.error("COMeT ConceptNet result Timeout")
        sentry_sdk.capture_exception(e)
        comet_result = requests.Response()
        comet_result.status_code = 504

    if comet_result.status_code != 200:
        msg = "COMeT ConceptNet: result status code is not 200: {}. result text: {}; result status: {}".format(
            comet_result, comet_result.text, comet_result.status_code
        )
        logger.warning(msg)
        relation_phrases = []
    else:
        relation_phrases = comet_result.json().get(relation, {}).get("beams", [])
    # remove `none` relation phrases (it's sometimes returned by COMeT)
    relation_phrases = [el for el in relation_phrases if el != "none"]

    if return_not_filtered and return_all:
        return relation_phrases

    relation_phrases = remove_duplicates([topic] + relation_phrases)[1:]  # the first element is topic
    relation_phrases = remove_all_phrases_containing_word(topic, relation_phrases)

    # check of sentiment for relation and drop it, if negative
    relation_phrases = [ph for ph in relation_phrases if len(ph) > 0 and get_nltk_sentiment(ph) != "negative"]
    relation_phrases = correct_verb_form(relation, relation_phrases)

    if return_all:
        return relation_phrases
    else:
        if len(relation_phrases) > 0:
            return choice(relation_phrases)
        else:
            return ""


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
        if token.pos == VERB:
            to_replace = token.text
            gerund = transform_vbg(token.lemma_)
            break
    if len(gerund) == 0:
        to_replace = topic.split()[0]
        gerund = transform_vbg(to_replace)

    return topic.replace(to_replace, gerund)


def get_used_attributes_by_name(
    utterances,
    attribute_name="meta_script_topic",
    value_by_default=None,
    activated=True,
    skill_name="meta_script_skill",
):
    """
    Find among given utterances values of particular attribute of `meta_script_skill` outputs.
    `meta_script_skill` should be active skill if `activated`

    Args:
        utterances: list of utterances. the first one is user's one.
        attribute_name: name of the attribute to collect
        value_by_default: if not None will also be added to the returned list
        activated: whether `meta_script_skill` should be active or not

    Returns:
        list of attribute values
    """
    used = []
    meta_script_outputs = get_skill_outputs_from_dialog(utterances, skill_name=skill_name, activated=activated)

    for output in meta_script_outputs:
        value = output.get(attribute_name, value_by_default)
        if value is not None:
            used.append(value)

    logger.info(f"Found used attribute `{attribute_name}` values:`{used}`")
    return used


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


def get_all_not_used_templates(used_templates, all_templates):
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
        return available
    else:
        return all_templates


def get_starting_phrase(dialog, topic, attr):
    """
    For considered topic propose starting phrase for meta-script, assign attributes for dialog

    Args:
        topic: current topic `verb + adj/adv/noun`
        attr: dictionary of current attributes

    Returns:
        tuple of text response, confidence and response attributes
    """
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_starting_template", value_by_default=None, activated=True
    )[-3:]

    if is_custom_topic(topic):
        template = get_not_used_template(used_templates, meta_script_skill_constants.OTHER_STARTINGS)
        attr["meta_script_starting_template"] = template
        response = template.replace("DOINGTHAT", get_gerund_topic(topic)).replace("DOTHAT", topic)
    elif is_wiki_topic(topic):
        template = get_not_used_template(used_templates, meta_script_skill_constants.WIKI_STARTINGS)
        attr["meta_script_starting_template"] = template
        response = template.replace("DESCRIPTION", WIKI_DESCRIPTIONS[topic])
    else:
        # predefined topic
        template = get_not_used_template(used_templates, meta_script_skill_constants.LET_ME_ASK_TEMPLATES)
        attr["meta_script_starting_template"] = template
        response = f"{template} {meta_script_skill_constants.STARTINGS[topic]}"

    confidence = meta_script_skill_constants.DEFAULT_STARTING_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE_SCENARIO
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
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_comment_template", value_by_default=None, activated=True
    )[-2:]

    sentiment = get_sentiment(dialog["human_utterances"][-1], probs=False)[0]
    template = get_not_used_template(used_templates, meta_script_skill_constants.COMMENTS[sentiment])
    attr["meta_script_comment_template"] = template
    response = template
    confidence = meta_script_skill_constants.DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_NOT_CONTINUE
    return response, confidence, attr


def get_opinion_phrase(dialog, topic, attr):
    """
    For considered topic propose opinion request phrase (one after dive deeper multi-step stage)
    for meta-script, assign attributes for dialog.

    Args:
        topic: current topic `verb + adj/adv/noun`
        attr: dictionary of current attributes

    Returns:
        tuple of text response, confidence and response attributes
    """
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_opinion_template", value_by_default=None, activated=True
    )[-2:]

    template = get_not_used_template(used_templates, meta_script_skill_constants.ASK_OPINION)
    attr["meta_script_opinion_template"] = template

    response = template.replace("DOINGTHAT", get_gerund_topic(topic)).replace("DOTHAT", topic)
    confidence = meta_script_skill_constants.DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE_SCENARIO
    return response, confidence, attr


def get_statement_phrase(dialog, topic, attr, TOPICS):
    """
    For considered topic propose dive deeper questions
    for meta-script, assign attributes for dialog.

    Args:
        topic: current topic `verb + adj/adv/noun`
        attr: dictionary of current attributes

    Returns:
        tuple of text response, confidence and response attributes
    """
    last_uttr = dialog["utterances"][-1]

    # choose and fill template with relation from COMeT
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_relation_template", value_by_default=None, activated=True
    )[-2:]
    meta_script_template = get_not_used_template(
        used_templates, meta_script_skill_constants.DIVE_DEEPER_TEMPLATE_COMETS
    )
    attr["meta_script_relation_template"] = meta_script_template

    relation = meta_script_skill_constants.DIVE_DEEPER_TEMPLATE_COMETS[meta_script_template]["attribute"]
    prediction = get_comet_atomic(f"person {topic}", relation, TOPICS)

    if prediction == "":
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}

    if (
        random() < 0.5
        and len(dialog["utterances"]) >= 2
        and dialog["bot_utterances"][-1].get("active_skill", "") == "meta_script_skill"
    ):
        dothat = "do that"
        doingthat = "doing that"
    else:
        dothat = re.sub(r"^be ", "become ", topic)
        doingthat = get_gerund_topic(topic)
    statement = (
        meta_script_template.replace("DOINGTHAT", doingthat).replace("DOTHAT", dothat).replace("RELATION", prediction)
    )

    # choose template for short comment
    used_templates = get_used_attributes_by_name(
        dialog["utterances"],
        attribute_name="meta_script_deeper_comment_template",
        value_by_default=None,
        activated=True,
    )[-2:]
    if is_yes(last_uttr):
        comment = get_not_used_template(
            used_templates,
            meta_script_skill_constants.DIVE_DEEPER_COMMENTS["yes"]
            + meta_script_skill_constants.DIVE_DEEPER_COMMENTS["other"],
        )
        attr["meta_script_deeper_comment_template"] = comment
    elif is_no(last_uttr):
        comment = get_not_used_template(
            used_templates,
            meta_script_skill_constants.DIVE_DEEPER_COMMENTS["no"]
            + meta_script_skill_constants.DIVE_DEEPER_COMMENTS["other"],
        )
        attr["meta_script_deeper_comment_template"] = comment
    else:
        comment = get_not_used_template(used_templates, meta_script_skill_constants.DIVE_DEEPER_COMMENTS["other"])
        attr["meta_script_deeper_comment_template"] = comment

    # choose and fill template of question upon relation from COMeT
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_question_template", value_by_default=None, activated=True
    )[-3:]
    meta_script_template_question = get_not_used_template(
        used_templates, meta_script_skill_constants.DIVE_DEEPER_TEMPLATE_COMETS[meta_script_template]["templates"]
    )
    attr["meta_script_question_template"] = meta_script_template_question

    if is_custom_topic(topic):
        response = f"{meta_script_template_question.replace('STATEMENT', statement)}".strip()
        confidence = meta_script_skill_constants.CONTINUE_USER_TOPIC_CONFIDENCE
    else:
        response = f"{comment} {meta_script_template_question.replace('STATEMENT', statement)}".strip()
        confidence = meta_script_skill_constants.DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE_SCENARIO
    return response, confidence, attr


def get_most_frequent_bigrams_with_word(word):
    target_bigrams = []
    for bigram in TOP_FREQUENT_BIGRAMS_TO_FIND_VERB:
        if re.search(r"\b%s\b" % word, bigram):
            target_bigrams += [bigram]
    return target_bigrams[:10]


def clean_up_topic_list(verb_nounphrases):
    """check whether - bigram not in `TOP_FREQUENT_BIGRAMS_TO_IGNORE`,
                     - verb not in `BANNED_VERBS`,
                     - noun not in `BANNED_NOUNS` + `TOP_100_FREQUENT_WORDS`
                     - at least one of the words not in `TOP_1k_FREQUENT_WORDS`

    Args:
        verb_nounphrases: list of verb+noun phrases

    Returns:
        list of verb+noun phrases satisfying requirements above
    """
    cleaned = []

    for vnp in verb_nounphrases:
        tokens = vnp.split()
        vnp_is_frequent = (
            vnp in TOP_FREQUENT_BIGRAMS_TO_IGNORE
            or tokens[0] in meta_script_skill_constants.BANNED_VERBS
            or tokens[-1] in meta_script_skill_constants.BANNED_NOUNS.union(TOP_100_FREQUENT_WORDS)
        )
        length_is_enough = len(tokens[0]) >= 2 and len(tokens[-1]) > 2
        one_of_verb_noun_not_frequent = (
            tokens[0] not in TOP_1k_FREQUENT_WORDS or tokens[-1] not in TOP_1k_FREQUENT_WORDS
        )
        verb_exceptions = ["play", "practice", "be"]

        if vnp in verb_exceptions or (not vnp_is_frequent and length_is_enough and one_of_verb_noun_not_frequent):
            if vnp[:3] == "be " and len(vnp[3:].split()) == 1:
                tokenized_comet_prediction = [ch.split() for ch in get_comet_conceptnet(vnp[3:], "IsA") if len(ch) > 0]
                tokenized_comet_prediction = [ch for ch in tokenized_comet_prediction if len(ch) > 0]
                is_person = any([ch[0] == "person" for ch in tokenized_comet_prediction])
                if is_person:
                    cleaned.append(vnp)
                else:
                    logger.info(f"Drop bigram {vnp} because in form `be something` not `be person`.")
            else:
                cleaned.append(vnp)
        else:
            logger.info(f"Drop bigram {vnp} because in top frequency lists.")
    return cleaned


def extract_verb_noun_phrases(utterance, only_i_do_that=True, nounphrases=None):
    nounphrases = [] if nounphrases is None else nounphrases
    verb_noun_phrases = []
    # verbs_without_nouns = []
    doc = nlp(utterance, disable=["ner"])
    for possible_verb in doc:
        if (
            possible_verb.pos == VERB
            and possible_verb.lemma_ not in meta_script_skill_constants.BANNED_VERBS
            and len(possible_verb.lemma_) > 1
        ):
            i_do_that = False
            for possible_subject in possible_verb.children:
                # if this verb is directed by `I`
                if possible_subject.dep == nsubj and possible_subject.text.lower() == "i":
                    i_do_that = True
                    break
            if not i_do_that:
                # if this verb is not directed by `I`, check whether this is a complex verb directed by `I`
                head_of_verb = possible_verb.head
                complex_verb = False
                # if no head for word, the head is the word itself
                if head_of_verb.text != possible_verb.text:
                    for head_verb_child in head_of_verb.children:
                        if head_verb_child.text == possible_verb.text:
                            if head_verb_child.dep == xcomp:
                                complex_verb = True
                        if head_verb_child.dep == nsubj and head_verb_child.text.lower() == "i":
                            i_do_that = True
                i_do_that *= complex_verb
            if (only_i_do_that and i_do_that) or not only_i_do_that:
                # if possible_verb.lemma_ not in TOP_1k_FREQUENT_WORDS:
                #     verbs_without_nouns.append(f"{possible_verb.lemma_}")
                for possible_subject in possible_verb.children:
                    if possible_subject.dep != nsubj:
                        if possible_subject.pos == NOUN and possible_subject.dep == dobj:
                            if (
                                possible_verb.lemma_ not in TOP_1k_FREQUENT_WORDS
                                or possible_subject.lemma_ not in TOP_1k_FREQUENT_WORDS
                            ) and possible_subject.lemma_ not in meta_script_skill_constants.BANNED_NOUNS:
                                verb_noun_phrases.append(f"{possible_verb.lemma_} {possible_subject}")
                                break
                        elif possible_subject.pos == ADP:
                            for poss_subsubj in possible_subject.children:
                                if poss_subsubj.pos == NOUN and poss_subsubj.dep == dobj:
                                    if (
                                        possible_verb.lemma_ not in TOP_1k_FREQUENT_WORDS
                                        or poss_subsubj.lemma_ not in TOP_1k_FREQUENT_WORDS
                                    ) and poss_subsubj.lemma_ not in meta_script_skill_constants.BANNED_NOUNS:
                                        verb_noun_phrases.append(
                                            f"{possible_verb.lemma_} {possible_subject} {poss_subsubj}"
                                        )
                                        break

    logger.info(f"Extracted the following verb-noun-based bigrams: {verb_noun_phrases}")
    good_verb_noun_phrases = clean_up_topic_list(verb_noun_phrases)
    sources = [meta_script_skill_constants.VNP_SOURCE] * len(good_verb_noun_phrases)
    logger.info(f"After cleaning we have the following verb-noun-based bigrams: {good_verb_noun_phrases}")

    if len(nounphrases) > 0:
        logger.info("No good verb-nounphrase topic. Try to find nounphrase, and appropriate verb from top-bigrams.")
        nounphrases = [
            re.sub(meta_script_skill_constants.possessive_pronouns, "", noun.lower()).strip() for noun in nounphrases
        ]
        nounphrases = [noun for noun in nounphrases if len(noun) > 0]
        noun_based_phrases = []
        for noun in nounphrases:
            noun_based_phrases += get_most_frequent_bigrams_with_word(noun)
        noun_based_phrases = [phrase for phrase in noun_based_phrases if len(phrase) > 0]
        logger.info(f"Extracted the following noun-based bigrams: {noun_based_phrases}")
        noun_based_phrases = clean_up_topic_list(noun_based_phrases)
        logger.info(f"After cleaning we have the following noun-based bigrams: {noun_based_phrases}")
        sources += [meta_script_skill_constants.NP_SOURCE] * len(noun_based_phrases)
        good_verb_noun_phrases += noun_based_phrases

    logger.info(f"extracted verb noun phrases {good_verb_noun_phrases} from {utterance}")
    return good_verb_noun_phrases, sources


def get_verb_noun_lemmas(topic):
    doc = nlp(topic, disable=["ner"])
    return [doc[0].lemma_, doc[-1].lemma_]


def check_topic_lemmas_in_sentence(sentence, topic):
    vn_lemmas = get_verb_noun_lemmas(topic.lower())
    sent_lemmas = [word.lemma_ for word in nlp(sentence.lower(), disable=["ner"])]
    vn_lemmas = set(vn_lemmas)
    for top_word in TOP_100_FREQUENT_WORDS:
        vn_lemmas.discard(top_word)

    for word in vn_lemmas:
        if word in sent_lemmas:
            return True
    return False
