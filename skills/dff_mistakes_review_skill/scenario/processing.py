import logging
import os
import random
import json

from . import response as loc_rsp

from df_engine.core import Context, Actor

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# def set_mistakes_review():
#     def set_mistakes_review_handler(ctx: Context, actor: Actor):
#         if not ctx.validation:
#             description = loc_rsp.feedback_response()
#             logger.info(f"""description: {description}""")
#             ctx.misc["agent"]["response"].update({"mistakes_review": description})
#         return ctx

#     return set_mistakes_review_handler


def set_mistakes_review():
    def set_mistakes_review_handler(ctx: Context, actor: Actor):
        if not ctx.validation:
            counter_mistakes_answers = 0
            human_utterances = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
            attributes = human_utterances.get("user", {}).get("attributes", {})
            mistakes_state = attributes.get("language_mistakes", "")
            if mistakes_state == "":
                ctx.misc["agent"]["response"].update({"mistakes_review": "Your answers were perfect! Nice work!"})
                return ctx

            mistakes_state = json.loads(mistakes_state)
            if mistakes_state["state"] == []:
                ctx.misc["agent"]["response"].update({"mistakes_review": "Your answers were perfect! Nice work!"})
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
                "context",
                "extra art",
                "extra prep",
                "skip art",
                "skip prep",
                "omis",
                "extra word",
                "wrong_word",
                "reason_3",
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
                ctx.misc["agent"]["response"].update({"mistakes_review": "Your answers were perfect! Nice work!"})
                return ctx

            ctx.misc["agent"]["response"].update({"mistakes_review": feedback_sents})
        return ctx

    return set_mistakes_review_handler
