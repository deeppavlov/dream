import json
import logging
import os
import random
import re
from collections import Counter

import pandas as pd
import spacy
from common.utils import join_words_in_or_pattern
from df_engine.core import Context, Actor
from . import response as loc_rsp


LANGUAGE = os.getenv("LANGUAGE")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_model = spacy.load("en_core_web_sm", disable=["parser", "ner"])
if LANGUAGE == "EN":
    df = pd.read_csv("common/dream_tutor/cerf_british.tsv", sep="\t")
else:
    df = pd.read_csv("common/dream_tutor/cerf_american.tsv", sep="\t")

# All 10k words?? I thought we would consider only 1k-2k depending on your estimation
with open("common/google-10000-english-no-swears.txt") as f:
    STOPWORDS = f.readlines()[:2000]

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
words_cerf = {level: list(df[df["cerf"] == level]["word"]) for level in LEVELS}
for level in LEVELS:
    words_cerf[level] = [word for word in words_cerf[level] if word not in STOPWORDS]

brackets_pattern = re.compile("[\(].*?[\)]")
etc_pattern = re.compile(", etc.", re.IGNORECASE)
spaces_pattern = re.compile(r"\s+")
smth_pattern = re.compile(r"(\(sb's\)|sb's|sth|sth/sb|sb/sth|; )", re.IGNORECASE)
starting_pattern = re.compile(r"^(to |a |the )", re.IGNORECASE)
stars_pattern = re.compile(r"\* \* \*")
space_re_pattern = re.compile(r"\. \* \?")


def preprocess_words(phrase):
    phrase = brackets_pattern.sub(".*?", phrase)
    phrase = etc_pattern.sub("", phrase)
    phrase = smth_pattern.sub(".*?", phrase)
    phrase = spaces_pattern.sub(" ", phrase)
    phrase = phrase.strip()
    phrase = starting_pattern.sub("", phrase)
    doc_phrase = load_model(phrase)
    phrase = " ".join([token.lemma_ for token in doc_phrase])
    phrase = stars_pattern.sub(".*?", phrase)
    phrase = space_re_pattern.sub(".*?", phrase)
    phrase = phrase.strip()
    return phrase


cerf_mapping = {}
for key, value in words_cerf.items():
    cerf_mapping[key] = [preprocess_words(phrase) for phrase in value]

PHRASES_PATTERN = {}
for key, value in cerf_mapping.items():
    PHRASES_PATTERN[key] = re.compile(join_words_in_or_pattern(value), re.IGNORECASE)


def check_cerf(lemmas):
    user_cerf = {}
    counter = 0
    for key, value in PHRASES_PATTERN.items():
        found_phrases = value.findall(" ".join(lemmas))
        found_phrases = list(set(found_phrases))
        found_phrases = [phrase for phrase in found_phrases if (len(phrase) < 30)]
        user_cerf[key] = found_phrases
        counter += len(found_phrases)

    count_cerf = {}
    for key, value in user_cerf.items():
        count_cerf[key] = round((len(value) / counter) * 100, 2)

    return user_cerf, count_cerf


def set_mistakes_review():
    def set_mistakes_review_handler(ctx: Context, actor: Actor):
        if not ctx.validation:
            review = {}
            types_mistakes, subtypes_mistakes = [], []
            counter_mistakes_answers = 0
            human_utterances = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
            attributes = human_utterances.get("user", {}).get("attributes", {})
            practice_skill_state = attributes.get("dff_language_practice_skill_state", {})
            mistakes_state = attributes.get("language_mistakes", "")
            user_utterances = attributes.get("user_utterances", [])
            lemmatized_user_utt = loc_rsp.lemmatize_utt(user_utterances)
            user_cerf, count_cerf = check_cerf(lemmatized_user_utt)
            review["vocabulary_cerf_percentages"] = count_cerf
            review["vocabulary_by_cerf"] = user_cerf
            try:
                scenario_name = practice_skill_state["shared_memory"]["dialog_script_name"]
                vocabulary_reply, percentage = loc_rsp.check_vocabulary(lemmatized_user_utt, scenario_name)
            except Exception:
                vocabulary_reply = ""

            if mistakes_state == "":
                reply = "Your answers were perfect! Nice work!" + "\n\n" + vocabulary_reply
                review["text"] = reply
                review["pecentage_vocabulary_used"] = percentage
                ctx.misc["agent"]["response"].update({"mistakes_review": review})
                return ctx

            mistakes_state = json.loads(mistakes_state)
            if mistakes_state["state"] == []:
                reply = "Your answers were perfect! Nice work!" + "\n\n" + vocabulary_reply
                review["text"] = reply
                review["pecentage_vocabulary_used"] = percentage
                ctx.misc["agent"]["response"].update({"mistakes_review": review})
                return ctx

            expl_templates = ["You used the wrong X. ", "The X was incorrect. ", "There was a mistake in the X. "]
            comp_templates = [
                """You said "X", but it would be better to say "Z". """,
                """You said "X", but the accurate way to say it would be "Z". """,
                """Instead of saying "X", I would suggest saying "Z". """,
            ]
            corr_templates = [
                """So, it would me more accurate to say "X". """,
                """Thus, it would be better to say "X". """,
                """That is why it would be more accurate to say "X". """,
            ]
            unique_subtypes = [
                "usage of a word",
                "extra article",
                "extra preposition",
                "skipped article",
                "skipped preposition",
                "omissed word",
                "extra word",
                "other",
                "did not use the article",
            ]
            feedback_sents = "You did good, but you made a few mistakes I'd love to discuss: \n\n"
            for state in mistakes_state["state"]:
                original_sentence = state[0]["original_sentence"]
                if original_sentence[-1] not in [".", "!", "?"]:
                    original_sentence += "."

                corrected_sentence = state[0]["corrected_sentence"]
                if original_sentence.replace(",", "").lower() == corrected_sentence.replace(",", "").lower():
                    continue
                elif original_sentence.replace(".", "").lower() == corrected_sentence.replace(".", "").lower():
                    continue

                elif original_sentence.replace("?", "").lower() == corrected_sentence.replace("?", "").lower():
                    continue

                counter_mistakes_answers += 1
                comp_template = random.choice(comp_templates)
                sentence_compare = comp_template.replace("X", original_sentence).replace("Z", corrected_sentence)
                feedback_sents += sentence_compare
                for selection in state[0]["selections"]:
                    correction = selection["correction"]
                    start_selection = selection["startSelection"]
                    end_selection = selection["endSelection"]
                    selection2correct = original_sentence[start_selection:end_selection]
                    if selection2correct.replace(",", "").lower() == correction.replace(",", "").lower():
                        continue
                    elif (correction[:2] == ", ") and selection2correct.lower() == correction[2:].lower():
                        continue

                    elif (correction[:2] == ". ") and selection2correct.lower() == correction[2:].lower():
                        continue

                    elif (correction[:2] == "? ") and selection2correct.lower() == correction[2:].lower():
                        continue

                    elif correction in [".", ",", "?"]:
                        continue

                    types_mistakes.append(selection["type"])
                    subtypes_mistakes.append(selection["subtype"])
                    if selection["subtype"] in unique_subtypes:
                        feedback_sents += selection["explanation"]
                    else:
                        expl_template = random.choice(expl_templates)
                        feedback_sents += expl_template.replace("X", selection["explanation"])

                    if correction != "":
                        corr_template = random.choice(corr_templates)
                        corrected_sent = corr_template.replace("X", correction)
                        feedback_sents += corrected_sent
                        feedback_sents += "\n"

                feedback_sents += "\n\n"

            if counter_mistakes_answers == 0:
                reply = "Your answers were perfect! Nice work!" + "\n\n" + vocabulary_reply
                review["text"] = reply
                review["pecentage_vocabulary_used"] = percentage
                ctx.misc["agent"]["response"].update({"mistakes_review": review})
                return ctx

            reply = feedback_sents + vocabulary_reply
            review["text"] = reply
            review["pecentage_vocabulary_used"] = percentage
            review["mistakes_counter"] = counter_mistakes_answers
            count_types = dict(Counter(types_mistakes))
            review["mistakes_types_counter"] = count_types
            count_subtypes = dict(Counter(subtypes_mistakes))
            review["mistakes_subtypes_counter"] = count_subtypes
            ctx.misc["agent"]["response"].update({"mistakes_review": review})

        return ctx

    return set_mistakes_review_handler
