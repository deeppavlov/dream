import asyncio
import logging
import time
from os import getenv
from typing import Dict, Callable

import sentry_sdk

from common.link import get_previously_active_skill
from common.robot import command_intents
from common.universal_templates import is_any_question_sentence_in_utterance
from common.utils import get_factoid, get_intents, high_priority_intents


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

HIGH_PRIORITY_INTENTS = int(getenv("HIGH_PRIORITY_INTENTS", 1))
RESTRICTION_FOR_SENSITIVE_CASE = int(getenv("RESTRICTION_FOR_SENSITIVE_CASE", 1))
ALWAYS_TURN_ON_ALL_SKILLS = int(getenv("ALWAYS_TURN_ON_ALL_SKILLS", 0))


class DescriptionBasedSkillSelectorConnector:
    async def send(self, payload: Dict, callback: Callable):
        st_time = time.time()
        try:
            dialog = payload["payload"]["states_batch"][0]

            skills_for_uttr = []
            user_uttr = dialog["human_utterances"][-1]

            intent_catcher_intents = get_intents(user_uttr, probs=False, which="intent_catcher")
            high_priority_intent_detected = any(
                [k for k in intent_catcher_intents if k in high_priority_intents["dff_intent_responder_skill"]]
            )
            command_detected = any([k for k in intent_catcher_intents if k in command_intents])

            if ALWAYS_TURN_ON_ALL_SKILLS or user_uttr["attributes"].get("selected_skills", None) in ["all", []]:
                logger.info("Selected skills: ALL")
                total_time = time.time() - st_time
                logger.info(f"description_based_skill_selector exec time = {total_time:.3f}s")
                # returning empty list of skills means trigger ALL skills for deeppavlov agent
                asyncio.create_task(callback(task_id=payload["task_id"], response=[]))
                return
            elif len(user_uttr["attributes"].get("selected_skills", [])) > 0:
                # can consider list os skill names or single skill name
                skills_for_uttr = user_uttr["attributes"].get("selected_skills", [])
                if isinstance(skills_for_uttr, str):
                    skills_for_uttr = [skills_for_uttr]
                logger.info(f"Selected skills: {skills_for_uttr}")
                total_time = time.time() - st_time
                logger.info(f"description_based_skill_selector exec time = {total_time:.3f}s")
                asyncio.create_task(callback(task_id=payload["task_id"], response=list(set(skills_for_uttr))))
                return
            elif high_priority_intent_detected and HIGH_PRIORITY_INTENTS:
                skills_for_uttr.append("dummy_skill")
                # process intent with corresponding IntentResponder
                skills_for_uttr.append("dff_intent_responder_skill")
                asyncio.create_task(callback(task_id=payload["task_id"], response=list(set(skills_for_uttr))))
                return
            elif command_detected and HIGH_PRIORITY_INTENTS:
                skills_for_uttr.append("dummy_skill")
                # process intent with corresponding IntentResponder
                skills_for_uttr.append("dff_command_selector_skill")
                asyncio.create_task(callback(task_id=payload["task_id"], response=list(set(skills_for_uttr))))
                return

            user_uttr_text = user_uttr["text"].lower()
            user_uttr_annotations = user_uttr["annotations"]

            all_skill_names = dialog.get("attributes", {}).get("pipeline", [])
            all_skill_names = [el.split(".")[1] for el in all_skill_names if "skills" in el]
            prompted_skills = [skill for skill in all_skill_names if "prompted_skill" in skill]

            not_prompted_skills = set(all_skill_names).difference(set(prompted_skills))

            # remove some skills as they will be added in specific cases
            not_prompted_skills.discard("factoid_qa")
            not_prompted_skills.discard("dff_google_api_skill")
            not_prompted_skills.discard("dff_document_qa_llm_skill")

            not_prompted_skills = list(not_prompted_skills)
            if dialog.get("bot", {}).get("attributes", {}).get("db_link", ""):
                # adding dff_document_qa_llm_skill only if we have trained model files in this dialog
                # (thus checking bot attributes)
                skills_for_uttr.append("dff_document_qa_llm_skill")
            is_factoid = "is_factoid" in get_factoid(user_uttr, probs=False)

            if user_uttr_text == "/get_dialog_id":
                skills_for_uttr = ["dummy_skill"]
            else:
                skills_for_uttr.append("dummy_skill")
                # adding linked-to skills
                skills_for_uttr.extend(get_previously_active_skill(dialog))

                if "dff_universal_prompted_skill" in prompted_skills:
                    skills_for_uttr.append("dff_universal_prompted_skill")

                # turn on skills if prompts are selected by prompt_selector
                ranged_prompts = user_uttr_annotations.get("prompt_selector", {}).get("prompts", [])
                if ranged_prompts:
                    for prompt_name in ranged_prompts:
                        if f"dff_{prompt_name}_prompted_skill" in prompted_skills:
                            skills_for_uttr.append(f"dff_{prompt_name}_prompted_skill")
                else:
                    skills_for_uttr.extend(prompted_skills)
                    logger.info("Adding all prompted skills as prompt selector did not select anything.")

                if is_any_question_sentence_in_utterance(dialog["human_utterances"][-1]):
                    skills_for_uttr.append("dff_google_api_skill")

                if is_factoid:
                    skills_for_uttr.append("factoid_qa")

                # turn on all other skills from pipeline that are not prompted
                skills_for_uttr.extend(not_prompted_skills)

            logger.info(f"Selected skills: {skills_for_uttr}")
            total_time = time.time() - st_time
            logger.info(f"description_based_skill_selector exec time = {total_time:.3f}s")
            asyncio.create_task(callback(task_id=payload["task_id"], response=list(set(skills_for_uttr))))
        except Exception as e:
            total_time = time.time() - st_time
            logger.info(f"description_based_skill_selector exec time = {total_time:.3f}s")
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(
                callback(
                    task_id=payload["task_id"],
                    response=["dummy_skill"],
                )
            )
