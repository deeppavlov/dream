import logging
import os
import en_core_web_sm
import inflect
import nltk
import sentry_sdk

from common.animals import ANIMAL_BADLIST

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()
p = inflect.engine()

nltk.download("punkt")

with open("animals_list.txt", "r") as fl:
    lines = fl.readlines()
    animals_list = {line.strip().lower() for line in lines}


def plural_nouns(text):
    plural_text = text
    try:
        processed_text = nlp(text)
        processed_tokens = []
        for token in processed_text:
            if token.tag_ == "NNP":
                processed_tokens.append(p.plural_noun(token.text))
            else:
                processed_tokens.append(token.text)
        plural_text = " ".join(processed_tokens)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return plural_text


def lemmatize_substr(text):
    lemm_text = ""
    if text:
        pr_text = nlp(text)
        processed_tokens = []
        for token in pr_text:
            if token.tag_ in ["NNS", "NNP"] and p.singular_noun(token.text):
                processed_tokens.append(p.singular_noun(token.text))
            else:
                processed_tokens.append(token.text)
        lemm_text = " ".join(processed_tokens)
    return lemm_text


def find_in_animals_list(annotations):
    found_animal = ""
    cobot_entities = annotations.get("cobot_entities", {}).get("entities", [])
    for entity in cobot_entities:
        lemm_entity = lemmatize_substr(entity)
        if entity in animals_list and entity not in ANIMAL_BADLIST:
            found_animal = entity
        if lemm_entity in animals_list and entity not in ANIMAL_BADLIST:
            found_animal = lemm_entity
    return found_animal


def preprocess_fact_random_facts(annotations, found_animal):
    found_facts = []
    facts = annotations.get("fact_random", [])
    for fact_info in facts:
        if fact_info.get("entity_substr", "") == found_animal:
            fact_text = fact_info["fact"]
            sentences = nltk.sent_tokenize(fact_text)
            if sentences:
                found_facts.append({"sentences": sentences})
    return found_facts
