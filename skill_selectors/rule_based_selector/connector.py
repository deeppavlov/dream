import asyncio
import logging
import re
import time
from os import getenv
from typing import Dict, Callable

import sentry_sdk

from common.emotion import if_turn_on_emotion
from common.gossip import check_is_celebrity_mentioned
from common.link import get_linked_to_skills, get_previously_active_skill
from common.movies import extract_movies_names_from_annotations
from common.response_selection import UNPREDICTABLE_SKILLS
from common.sensitive import is_sensitive_topic_and_request
from common.skills_turn_on_topics_and_patterns import turn_on_skills
from common.universal_templates import if_chat_about_particular_topic, if_choose_topic, GREETING_QUESTIONS_TEXTS
from common.utils import (
    high_priority_intents,
    low_priority_intents,
    get_topics,
    get_intents,
    get_named_locations,
    get_factoid,
)
from common.weather import if_special_weather_turn_on
from common.wiki_skill import if_switch_wiki_skill, switch_wiki_skill_on_news, if_switch_test_skill
from common.utils import yes_templates


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
prev_scenarios = []


class RuleBasedSkillSelectorConnector:
    async def send(self, payload: Dict, callback: Callable):
        st_time = time.time()
        try:
            dialog = payload["payload"]["states_batch"][0]

            skills_for_uttr = []
            user_uttr = dialog["human_utterances"][-1]
            user_uttr_text = user_uttr["text"].lower()
            user_uttr_annotations = user_uttr["annotations"]
            bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
            bot_uttr_text_lower = bot_uttr.get("text", "").lower()
            prev_active_skill = bot_uttr.get("active_skill", "")

            intent_catcher_intents = get_intents(user_uttr, probs=False, which="intent_catcher")

            # agent = ctx.misc.get("agent", {})
            # dialog = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
            last_utterance = user_uttr.get("user", {})
            practice_skill_state = last_utterance.get("attributes", {}).get("dff_language_practice_skill_state", {})
            scenario_len = practice_skill_state.get("shared_memory", {}).get("scenario_len", 0)
            dialog_step_id = practice_skill_state.get("shared_memory", {}).get("dialog_step_id", 0)
            bot_uttr_text = bot_uttr.get("text", "")

            if "lets_chat_about" in intent_catcher_intents:
                skills_for_uttr.append("dff_language_practice_skill")
            elif (
                (prev_active_skill == "dff_language_practice_skill")
                and ((scenario_len - 1) != dialog_step_id)
                and (bot_uttr_text != "We can role play some discussions on different topics.")
                and (bot_uttr_text != "As you wish!")
            ):
                skills_for_uttr.append("dff_language_practice_skill")

            if (
                ((scenario_len - 1) == dialog_step_id)
                and (dialog_step_id != 0)
                and (prev_active_skill != "dff_mistakes_review_skill")
                and ("dff_language_practice_skill" not in skills_for_uttr)
            ):
                skills_for_uttr.append("dff_mistakes_review_skill")

            if bot_uttr_text == "Ok, let's finish here. Would you like me to comment on your performance?":
                if re.search(yes_templates, user_uttr_text):
                    skills_for_uttr = ["dff_mistakes_review_skill"]

            if not skills_for_uttr:
                skills_for_uttr.append("dff_friendship_skill")

            logger.info(f"Selected skills: {skills_for_uttr}")
            total_time = time.time() - st_time
            logger.info(f"rule_based_selector exec time = {total_time:.3f}s")
            # asyncio.create_task(callback(task_id=payload["task_id"], response=list(set(skills_for_uttr))))
            asyncio.create_task(callback(task_id=payload["task_id"], response=skills_for_uttr))
        except Exception as e:
            total_time = time.time() - st_time
            logger.info(f"rule_based_selector exec time = {total_time:.3f}s")
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=skills_for_uttr))
