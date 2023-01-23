import logging
import os
import random
import json
from collections import Counter
import pandas as pd
import spacy
import re

from . import response as loc_rsp

from df_engine.core import Context, Actor

LANGUAGE = os.getenv("LANGUAGE")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_model = spacy.load("en_core_web_sm", disable=["parser", "ner"])
if LANGUAGE == "EN":
    df = pd.read_csv("common/dream_tutor/cerf_british.tsv", sep="\t")
else:
    df = pd.read_csv("common/dream_tutor/cerf_american.tsv", sep="\t")

with open('common/google-10000-english-no-swears.txt') as f:
    stopwords = f.readlines()


words_cerf = list(df.word)
# words_level_cerf = list(df.cerf)
words_cerf = [word for word in words_cerf if word not in stopwords]

clear_words_cerf = []
for phrase in words_cerf:
    phrase = re.sub("[\(].*?[\)]", "", phrase)
    phrase = phrase.replace(", etc.", "")
    phrase = phrase.replace("  ", " ")
    phrase = phrase.replace("(sb's)", ".*?")
    phrase = phrase.replace("sb's", ".*?")
    phrase = phrase.replace("sth", ".*?")
    phrase = phrase.replace("sth/sb", ".*?")
    phrase = phrase.replace("sb/sth", ".*?")
    phrase = phrase.replace("; ", ".*?")
    if phrase[-1] == " ":
        phrase = phrase[:-1]
    if phrase[:3] == "to ":
        phrase = phrase[3:]
    elif phrase[:2] == "a ":
        phrase = phrase[2:]
    elif phrase[:4] == "the ":
        phrase = phrase[4:] 

    doc_phrase = load_model(phrase)
    phrase = " ".join([token.lemma_ for token in doc_phrase])
    phrase = phrase.replace("* * *", ".*?")
    clear_words_cerf.append(phrase)

PHRASES_PATTERN = re.compile(r"\b(" + ("|".join(clear_words_cerf) + ")"), re.IGNORECASE)


def check_cerf(lemmas):
    user_cerf = {}
    counter = 0
    uttes = " ".join(lemmas)
    logger.info(f"""utterances: {uttes}""")
    # found_phrases = re.findall(phrases_re, " ".join(lemmas), re.IGNORECASE)
    found_phrases = PHRASES_PATTERN.findall(" ".join(lemmas))
    found_phrases = list(set(found_phrases))
    logger.info(f"""found_phrases: {found_phrases}""")
    # logger.info(f"""words_cerf: {words_cerf}""")
    # logger.info(f"""clear_words_cerf: {clear_words_cerf}""")
    for found_phrase in found_phrases:
        counter += 1
        index_phrase = clear_words_cerf.index(found_phrase)
        not_lemmatized_phrase = words_cerf[index_phrase]
        df_word = df[df["word"] == not_lemmatized_phrase]
        cerf = list(df_word["cerf"])[0]
        if cerf not in user_cerf.keys():
            user_cerf[cerf] = [not_lemmatized_phrase]
        else:
            user_cerf[cerf].append(not_lemmatized_phrase)

    count_cerf = {}
    for key, value in user_cerf.items():
        count_cerf[key] = round((len(value) / counter) * 100, 2)

    logger.info(f"""user_cerf: {user_cerf}""")
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

            logger.info(f"mistakes_state = {mistakes_state}")

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
                    if selection2correct.lower() == correction.lower():
                        continue
                    elif (correction[:2] == ", ") and selection2correct.lower() == correction[2:].lower():
                        continue

                    elif (correction[:2] == ". ") and selection2correct.lower() == correction[2:].lower():
                        continue

                    elif (correction[:2] == "? ") and selection2correct.lower() == correction[2:].lower():
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
