#!/usr/bin/env python

import logging
from random import choice, random
import re
import string
import json
from os import getenv
import sentry_sdk
import spacy
import requests
from spacy.symbols import nsubj, VERB, xcomp, NOUN, ADP, dobj

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from common.utils import transform_vbg, get_skill_outputs_from_dialog, is_yes, is_no
from constants import COMET_SERVICE_URL, CONCEPTNET_SERVICE_URL, STARTINGS, OTHER_STARTINGS, WIKI_STARTINGS, \
    LET_ME_ASK_TEMPLATES, COMMENTS, ASK_OPINION, DIVE_DEEPER_TEMPLATE_COMETS, DIVE_DEEPER_COMMENTS, \
    DEFAULT_CONFIDENCE, DEFAULT_STARTING_CONFIDENCE, CONTINUE_USER_TOPIC_CONFIDENCE, BANNED_VERBS, BANNED_NOUNS, \
    VNP_SOURCE, NP_SOURCE


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


nlp = spacy.load("en_core_web_sm")

with open("topics_counter_10.json", "r") as f:
    # phrases appeared more than 500 times
    # phrases are like `verb + noun` or `verb + prep + noun` WITHOUT articles
    TOP_FREQUENT_VERB_NOUN_PHRASES = json.load(f)

# for 200 -> 933 bigrams, for 300 -> 556 bigrams, for 500 -> 273 bigrams to ignore
TOP_FREQUENT_BIGRAMS_TO_IGNORE = [bigram for bigram in TOP_FREQUENT_VERB_NOUN_PHRASES
                                  if TOP_FREQUENT_VERB_NOUN_PHRASES[bigram] >= 200]
# they are already sorted in decreasing order
TOP_FREQUENT_BIGRAMS_TO_FIND_VERB = {bigram: TOP_FREQUENT_VERB_NOUN_PHRASES[bigram]
                                     for bigram in TOP_FREQUENT_VERB_NOUN_PHRASES
                                     if TOP_FREQUENT_VERB_NOUN_PHRASES[bigram] < 200}

with open("google-10000-english-no-swears.txt", "r") as f:
    TOP_FREQUENT_WORDS = f.read().splitlines()[:1000]

WIKI_DESCRIPTIONS = json.load(open("wiki_topics_descriptions_one_sent.json", "r"))
list_of_hobbies = list(WIKI_DESCRIPTIONS.keys())


def get_verb_topic(nounphrased_topic):
    doc = nlp(nounphrased_topic)
    if len(doc) == 1:
        for token in doc:
            if token.pos == VERB:
                return (token.lemma_)
    return f"do {nounphrased_topic}"


for hobby in list_of_hobbies:
    verb_hobby = get_verb_topic(hobby)
    WIKI_DESCRIPTIONS[verb_hobby] = WIKI_DESCRIPTIONS.pop(hobby)

punct_reg = re.compile(f'[{string.punctuation}]')
articles_reg = re.compile(r'(a|the|to)\s')
person_reg = re.compile(r'^(person x|personx|person)\s')


def is_custom_topic(topic):
    return not (topic in STARTINGS or topic in WIKI_DESCRIPTIONS)


def is_wiki_topic(topic):
    return topic in WIKI_DESCRIPTIONS


def is_predefined_topic(topic):
    return topic in STARTINGS


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
            if v_clean.split()[0] not in ["feel", "need", "want"]:
                d[v_clean] += [v]
    return [re.sub(person_reg, '', v[0]) for k, v in d.items()]


def custom_request(url, data, timeout, method='POST'):
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
        for ["xIntent", "xNeed", "xWant", "oWant", "CapableOf", "Causes", "CausesDesire", "DesireOf",
             "Desires", "HasFirstSubevent", "HasLastSubevent", "HasPainCharacter", "HasPainIntensity",
             "HasPrerequisite", "HasSubevent", "MotivatedByGoal", "NotCapableOf", "NotDesires", "ReceivesAction"]
    """
    if attr in ["xIntent", "xNeed", "xWant", "oWant", "CapableOf", "Causes", "CausesDesire", "DesireOf",
                "Desires", "HasFirstSubevent", "HasLastSubevent", "HasPainCharacter", "HasPainIntensity",
                "HasPrerequisite", "HasSubevent", "MotivatedByGoal", "NotCapableOf", "NotDesires", "ReceivesAction"]:
        for i in range(len(values)):
            doc = nlp(values[i])

            if values[i][:3] != "to " and doc[0].pos == VERB:
                values[i] = "to " + values[i]
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
                    values[i] = doc[0].lemma_ + values[i][values[i].find(" "):]
            if values[i][:3] != "to " and doc[0].pos == VERB:
                values[i] = "to " + values[i]
    return values


def get_comet_atomic(topic, relation, TOPICS={}):
    """
    Get COMeT prediction for considered topic like `verb subj/adj/adv` of particular relation.

    Args:
        topic: string in form `verb subj/adj/adv`
        relation:  considered comet relations, out of ["xAttr", "xIntent", "xNeed", "xEffect", "xReact", "xWant"]

    Returns:
        string, one of predicted by Comet relations
    """

    logger.info(f"Comet Atomic request on topic: {topic}.")
    if topic is None or topic == "" or relation == "" or relation is None:
        return ""

    predefined_relation = TOPICS.get(topic, {}).get(relation, [])

    if len(predefined_relation) > 0:
        # already predefined `topic & relation` pair
        relation_phrases = predefined_relation
    else:
        # send request to COMeT service on `topic & relation`
        try:
            comet_result = custom_request(COMET_SERVICE_URL, {"input": f"Person {topic}.",
                                                              "category": relation}, 1.5)
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            logger.error("COMeT Atomic result Timeout")
            sentry_sdk.capture_exception(e)
            comet_result = requests.Response()
            comet_result.status_code = 504

        if comet_result.status_code != 200:
            msg = "COMeT Atomic: result status code is not 200: {}. result text: {}; result status: {}".format(
                comet_result, comet_result.text, comet_result.status_code)
            logger.warning(msg)
            relation_phrases = []
        else:
            relation_phrases = comet_result.json().get(relation, {}).get("beams", [])
    # remove `none` relation phrases (it's sometimes returned by COMeT)
    relation_phrases = [el for el in relation_phrases if el != "none"]

    relation_phrases = remove_duplicates([topic] + relation_phrases)[1:]  # the first element is topic

    relation_phrases = correct_verb_form(relation, relation_phrases)

    if len(relation_phrases) > 0:
        return choice(relation_phrases)
    else:
        return ""


def get_comet_conceptnet(topic, relation, return_all=False):
    """
    Get COMeT ConceptNet prediction for considered topic like `verb subj/adj/adv` of particular relation.

    Args:
        topic: string in form of nounphrase
        relation:  considered comet relations, out of ["xAttr", "xIntent", "xNeed", "xEffect", "xReact", "xWant"]

    Returns:
        string, one of predicted by Comet relations
    """

    logger.info(f"Comet ConceptNet request on topic: {topic}.")
    if topic is None or topic == "" or relation == "" or relation is None:
        return ""

    # send request to COMeT ConceptNet service on `topic & relation`
    try:
        comet_result = custom_request(CONCEPTNET_SERVICE_URL, {"input": f"{topic}.",
                                                               "category": relation}, 1.5)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.error("COMeT ConceptNet result Timeout")
        sentry_sdk.capture_exception(e)
        comet_result = requests.Response()
        comet_result.status_code = 504

    if comet_result.status_code != 200:
        msg = "COMeT ConceptNet: result status code is not 200: {}. result text: {}; result status: {}".format(
            comet_result, comet_result.text, comet_result.status_code)
        logger.warning(msg)
        relation_phrases = []
    else:
        relation_phrases = comet_result.json().get(relation, {}).get("beams", [])
    # remove `none` relation phrases (it's sometimes returned by COMeT)
    relation_phrases = [el for el in relation_phrases if el != "none"]

    banned = [topic, f"be {topic}", f"be a {topic}"]
    relation_phrases = remove_duplicates(banned + relation_phrases)[len(banned):]

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


def get_used_attributes_by_name(utterances, attribute_name="meta_script_topic", value_by_default=None, activated=True):
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
    meta_script_outputs = get_skill_outputs_from_dialog(
        utterances, skill_name="meta_script_skill", activated=activated)

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
        dialog["utterances"], attribute_name="meta_script_starting_template",
        value_by_default=None, activated=True)[-3:]

    if is_custom_topic(topic):
        template = get_not_used_template(used_templates, OTHER_STARTINGS)
        attr["meta_script_starting_template"] = template
        response = template.replace('DOINGTHAT', get_gerund_topic(topic)).replace('DOTHAT', topic)
    elif is_wiki_topic(topic):
        template = get_not_used_template(used_templates, WIKI_STARTINGS)
        attr["meta_script_starting_template"] = template
        response = template.replace('DESCRIPTION', WIKI_DESCRIPTIONS[topic])
    else:
        # predefined topic
        template = get_not_used_template(used_templates, LET_ME_ASK_TEMPLATES)
        attr["meta_script_starting_template"] = template
        response = f"{template} {STARTINGS[topic]}"

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
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_comment_template",
        value_by_default=None, activated=True)[-2:]

    sentiment = dialog["utterances"][-1]["annotations"].get("sentiment_classification",
                                                            {'text': ['neutral', 1.]})["text"][0]
    template = get_not_used_template(used_templates, COMMENTS[sentiment])
    attr["meta_script_comment_template"] = template
    response = template
    confidence = DEFAULT_CONFIDENCE
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
        dialog["utterances"], attribute_name="meta_script_opinion_template",
        value_by_default=None, activated=True)[-2:]

    template = get_not_used_template(used_templates, ASK_OPINION)
    attr["meta_script_opinion_template"] = template

    response = template.replace("DOINGTHAT", get_gerund_topic(topic)).replace("DOTHAT", topic)
    confidence = DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE
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
        dialog["utterances"], attribute_name="meta_script_relation_template",
        value_by_default=None, activated=True)[-2:]
    meta_script_template = get_not_used_template(used_templates, DIVE_DEEPER_TEMPLATE_COMETS)
    attr["meta_script_relation_template"] = meta_script_template

    relation = DIVE_DEEPER_TEMPLATE_COMETS[meta_script_template]["attribute"]
    prediction = get_comet_atomic(topic, relation, TOPICS)

    if prediction == "":
        return "", 0.0, {"can_continue": CAN_NOT_CONTINUE}

    if random() < 0.5 and len(dialog["utterances"]) >= 2 and dialog["bot_utterances"][-1].get(
            "active_skill", "") == "meta_script_skill":
        dothat = "do that"
        doingthat = "doing that"
    else:
        dothat = re.sub(r"^be ", "become ", topic)
        doingthat = get_gerund_topic(topic)
    statement = meta_script_template.replace(
        "DOINGTHAT", doingthat).replace(
        "DOTHAT", dothat).replace(
        "RELATION", prediction).replace(
        "person x ", "").replace(
        "personx ", "")

    # choose template for short comment
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_deeper_comment_template",
        value_by_default=None, activated=True)[-2:]
    if is_yes(last_uttr):
        comment = get_not_used_template(
            used_templates, DIVE_DEEPER_COMMENTS["yes"] + DIVE_DEEPER_COMMENTS["other"])
        attr["meta_script_deeper_comment_template"] = comment
    elif is_no(last_uttr):
        comment = get_not_used_template(
            used_templates, DIVE_DEEPER_COMMENTS["no"] + DIVE_DEEPER_COMMENTS["other"])
        attr["meta_script_deeper_comment_template"] = comment
    else:
        comment = get_not_used_template(
            used_templates, DIVE_DEEPER_COMMENTS["other"])
        attr["meta_script_deeper_comment_template"] = comment

    # choose and fill template of question upon relation from COMeT
    used_templates = get_used_attributes_by_name(
        dialog["utterances"], attribute_name="meta_script_question_template",
        value_by_default=None, activated=True)[-3:]
    meta_script_template_question = get_not_used_template(
        used_templates, DIVE_DEEPER_TEMPLATE_COMETS[meta_script_template]["templates"])
    attr["meta_script_question_template"] = meta_script_template_question

    if is_custom_topic(topic):
        response = f"{meta_script_template_question.replace('STATEMENT', statement)}".strip()
        confidence = CONTINUE_USER_TOPIC_CONFIDENCE
    else:
        response = f"{comment} {meta_script_template_question.replace('STATEMENT', statement)}".strip()
        confidence = DEFAULT_CONFIDENCE
    attr["can_continue"] = CAN_CONTINUE
    return response, confidence, attr


def get_most_frequent_bigrams_with_word(word):
    target_bigrams = []
    for bigram in TOP_FREQUENT_BIGRAMS_TO_FIND_VERB:
        if re.search(r'\b%s\b' % word, bigram):
            target_bigrams += [bigram]
    return target_bigrams[:10]


def clean_up_topic_list(verb_nounphrases):
    """check whether - bigram not in `TOP_FREQUENT_BIGRAMS_TO_IGNORE`,
                     - verb not in `BANNED_VERBS`,
                     - noun not in `BANNED_NOUNS` + 100 `TOP_FREQUENT_WORDS`
                     - at least one of the words not in `TOP_FREQUENT_WORDS`

    Args:
        verb_nounphrases: list of verb+noun phrases

    Returns:
        list of verb+noun phrases satisfying requirements above
    """
    cleaned = []

    for vnp in verb_nounphrases:
        tokens = vnp.split()
        if vnp not in TOP_FREQUENT_BIGRAMS_TO_IGNORE and tokens[0] not in BANNED_VERBS and \
                tokens[-1] not in BANNED_NOUNS + TOP_FREQUENT_WORDS[:100] and len(tokens[-1]) > 2 and \
                (tokens[0] not in TOP_FREQUENT_WORDS or tokens[-1] not in TOP_FREQUENT_WORDS):
            if vnp[:3] == "be " and len(vnp[3:].split()) == 1:
                is_person = "person" in get_comet_conceptnet(vnp[3:], "IsA")
                if is_person:
                    cleaned.append(vnp)
                else:
                    logger.info(f"Drop bigram {vnp} because in form `be something` not `be person`.")
            else:
                cleaned.append(vnp)
        else:
            logger.info(f"Drop bigram {vnp} because in top frequency lists.")
    return cleaned


relation_adj = re.compile(r"(my |your |yours |mine |their |our |her |his |its )")


def extract_verb_noun_phrases(utterance, only_i_do_that=True, nounphrases=[]):
    verb_noun_phrases = []
    # verbs_without_nouns = []
    doc = nlp(utterance, disable=["ner"])
    for possible_verb in doc:
        if possible_verb.pos == VERB and possible_verb.lemma_ not in BANNED_VERBS and len(possible_verb.lemma_) > 1:
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
                # if possible_verb.lemma_ not in TOP_FREQUENT_WORDS:
                #     verbs_without_nouns.append(f"{possible_verb.lemma_}")
                for possible_subject in possible_verb.children:
                    if possible_subject.dep != nsubj:
                        if possible_subject.pos == NOUN and possible_subject.dep == dobj:
                            if (possible_verb.lemma_ not in TOP_FREQUENT_WORDS or possible_subject.lemma_ not
                                in TOP_FREQUENT_WORDS) and \
                                    possible_subject.lemma_ not in BANNED_NOUNS:
                                verb_noun_phrases.append(f"{possible_verb.lemma_} {possible_subject}")
                                break
                        elif possible_subject.pos == ADP:
                            for poss_subsubj in possible_subject.children:
                                if poss_subsubj.pos == NOUN and poss_subsubj.dep == dobj:
                                    if (possible_verb.lemma_ not in TOP_FREQUENT_WORDS or poss_subsubj.lemma_ not
                                        in TOP_FREQUENT_WORDS) and \
                                            poss_subsubj.lemma_ not in BANNED_NOUNS:
                                        verb_noun_phrases.append(
                                            f"{possible_verb.lemma_} {possible_subject} {poss_subsubj}")
                                        break

    logger.info(f"Extracted the following bigrams: {verb_noun_phrases}")
    good_verb_noun_phrases = clean_up_topic_list(verb_noun_phrases)
    logger.info(f"After cleaning we have the following bigrams: {good_verb_noun_phrases}")

    if len(good_verb_noun_phrases) == 0 and len(nounphrases) > 0:
        logger.info("No good verb-nounphrase topic. Try to find nounphrase, and appropriate verb from top-bigrams.")
        nounphrases = [re.sub(relation_adj, "", noun.lower()).strip() for noun in nounphrases]
        for noun in nounphrases:
            good_verb_noun_phrases += get_most_frequent_bigrams_with_word(noun)
        good_verb_noun_phrases = [phrase for phrase in good_verb_noun_phrases if len(phrase) > 0]
        logger.info(f"Extracted the following bigrams: {good_verb_noun_phrases}")
        good_verb_noun_phrases = clean_up_topic_list(good_verb_noun_phrases)
        logger.info(f"After cleaning we have the following bigrams: {good_verb_noun_phrases}")
        source = NP_SOURCE
    else:
        source = VNP_SOURCE

    logger.info(f'extracted verb noun phrases {good_verb_noun_phrases} from {utterance}')
    return good_verb_noun_phrases, source


def get_verb_noun_lemmas(topic):
    doc = nlp(topic, disable=["ner"])
    return [doc[0].lemma_, doc[-1].lemma_]


def check_topic_lemmas_in_sentence(sentence, topic):
    vn_lemmas = get_verb_noun_lemmas(topic.lower())
    sent_lemmas = [word.lemma_ for word in nlp(sentence.lower(), disable=["ner"])]
    vn_lemmas = set(vn_lemmas)
    for top_word in TOP_FREQUENT_WORDS[:100]:
        vn_lemmas.discard(top_word)

    for word in vn_lemmas:
        if word in sent_lemmas:
            return True
    return False
