import logging
import json
import random
import re
import spacy

from df_engine.core import Context, Actor

load_model = spacy.load("en_core_web_sm", disable=["parser", "ner"])

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def lemmatize_utt(user_utterances: list):
    joined_utt = " ".join(user_utterances).lower()
    doc_utt = load_model(joined_utt)
    lemmas = [token.lemma_ for token in doc_utt]
    return lemmas


def check_vocabulary(user_utterances_lemmatized: list, scenario_name: str) -> str:
    scenario = json.load(open(f"data/{scenario_name}.json"))
    lemmatized_utt = " ".join(user_utterances_lemmatized)
    expected_phrases = scenario["expected_language"]
    used_phrases = []
    not_used_phrases = []
    for phrase in expected_phrases:
        pattern = phrase.replace("/", "|")
        if pattern[:3] == "To ":
            pattern = pattern[3:]
        pattern = re.sub("[\(].*?[\)]", "", pattern)
        pattern = pattern.replace("  ", " ")
        if pattern[-1] == " ":
            pattern = pattern[:-1]
        doc_pattern = load_model(pattern)
        pattern = " ".join([token.lemma_ for token in doc_pattern])
        logger.info(f"""pattern: {pattern}""")
        pattern = pattern.replace("* * *", ".*?")
        pattern = pattern.replace("...", "")
        pattern = pattern.replace("something", ".*?")
        pattern = pattern.replace("someone", ".*?")
        is_used = bool(re.findall(pattern, lemmatized_utt, re.IGNORECASE))
        if is_used:
            used_phrases.append(phrase)
        else:
            not_used_phrases.append(phrase)

    reply = ""
    if len(used_phrases) == 0:
        reply += """To make your speech sound more advanced you could use the following phrases:\n"""
        reply += "\n".join(not_used_phrases)

    elif len(used_phrases) == 1:
        reply += f"""You used one really nice phrase -- "{used_phrases[0]}". To make your speech sound more advanced you could also use the following phrases:\n"""
        reply += "\n".join(not_used_phrases)

    else:
        reply += """Your vocabulary was great! Here are the phrases that I really liked:\n"""
        reply += "\n".join(used_phrases)
        if 0 < len(not_used_phrases) <= 1:
            reply += f"""\n\nThere is one more useful phrase you could use - {not_used_phrases[0]}"""
        elif len(not_used_phrases) > 1:
            reply += """\n\nTo make your speech sound even more advanced you could also use the following phrases:\n"""
            reply += "\n".join(not_used_phrases)

    if len(used_phrases) == 0:
        percent_expected_lang_used = 0
    else:
        percent_expected_lang_used = round(((len(used_phrases) / len(expected_phrases)) * 100), 2)

    return reply, percent_expected_lang_used


def feedback_response():
    def feedback_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        counter_mistakes_answers = 0
        human_utterances = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
        attributes = human_utterances.get("user", {}).get("attributes", {})
        practice_skill_state = attributes.get("dff_language_practice_skill_state", {})
        mistakes_state = attributes.get("language_mistakes", "")
        user_utterances = attributes.get("user_utterances", [])
        lemmatized_user_utt = lemmatize_utt(user_utterances)
        try:
            scenario_name = practice_skill_state["shared_memory"]["dialog_script_name"]
            vocabulary_reply, percentage = check_vocabulary(lemmatized_user_utt, scenario_name)
        except Exception:
            vocabulary_reply = ""

        if mistakes_state == "":
            return "Your answers were perfect! Nice work!" + "\n\n" + vocabulary_reply
        mistakes_state = json.loads(mistakes_state)
        if mistakes_state["state"] == []:
            return "Your answers were perfect! Nice work!" + "\n\n" + vocabulary_reply

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
            return "Your answers were perfect! Nice work!" + "\n\n" + vocabulary_reply

        return feedback_sents + vocabulary_reply

    return feedback_response_handler
