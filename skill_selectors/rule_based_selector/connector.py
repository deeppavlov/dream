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


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
            high_priority_intent_detected = any(
                [k for k in intent_catcher_intents if k in high_priority_intents["dff_intent_responder_skill"]]
            )
            low_priority_intent_detected = any([k for k in intent_catcher_intents if k in low_priority_intents])

            detected_topics = set(get_topics(user_uttr, which="all"))

            is_factoid = get_factoid(user_uttr).get("is_factoid", 0.0) > 0.96
            is_celebrity_mentioned = check_is_celebrity_mentioned(user_uttr)

            if_choose_topic_detected = if_choose_topic(user_uttr, bot_uttr)
            if_lets_chat_about_particular_topic_detected = if_chat_about_particular_topic(user_uttr, bot_uttr)

            dialog_len = len(dialog["human_utterances"])

            exit_cond = "exit" in intent_catcher_intents and (
                dialog_len == 1 or (dialog_len == 2 and len(user_uttr_text.split()) > 3)
            )
            repeat_cond = (
                "repeat" in intent_catcher_intents
                and prev_active_skill in UNPREDICTABLE_SKILLS
                and re.match(r"^what.?$", user_uttr_text)
            )
            cant_do_cond = (
                "cant_do" in intent_catcher_intents
                and "play" in user_uttr_text
                and any([phrase in bot_uttr_text_lower for phrase in GREETING_QUESTIONS_TEXTS])
            )
            for intent_name, condition in zip(["exit", "repeat", "cant_do"], [exit_cond, repeat_cond, cant_do_cond]):
                if condition:
                    high_priority_intent_detected = False
                    not_detected = {"detected": 0, "confidence": 0.0}
                    user_uttr["annotations"]["intent_catcher"][intent_name] = not_detected
                    dialog["utterances"][-1]["annotations"]["intent_catcher"][intent_name] = not_detected

            if "/new_persona" in user_uttr_text:
                # process /new_persona command
                skills_for_uttr.append("personality_catcher")  # TODO: rm crutch of personality_catcher
            elif user_uttr_text == "/get_dialog_id":
                skills_for_uttr.append("dummy_skill")
            elif high_priority_intent_detected:
                skills_for_uttr.append("dummy_skill")
                # process intent with corresponding IntentResponder
                skills_for_uttr.append("dff_intent_responder_skill")
                skills_for_uttr.append("robot_skill")
            elif is_sensitive_topic_and_request(user_uttr):
                # process user utterance with sensitive content, "safe mode"

                # adding open-domain skills without opinion expression
                skills_for_uttr.append("dff_program_y_dangerous_skill")
                skills_for_uttr.append("meta_script_skill")
                skills_for_uttr.append("personal_info_skill")
                skills_for_uttr.append("factoid_qa")
                skills_for_uttr.append("dff_grounding_skill")
                # we have only russian version of dff_generative_skill
                skills_for_uttr.append("dff_generative_skill")
                skills_for_uttr.append("dummy_skill")
                skills_for_uttr.append("small_talk_skill")

                if if_lets_chat_about_particular_topic_detected:
                    skills_for_uttr.append("news_api_skill")
                if if_special_weather_turn_on(user_uttr, bot_uttr):
                    skills_for_uttr.append("dff_weather_skill")
                if is_celebrity_mentioned:
                    skills_for_uttr.append("dff_gossip_skill")

                # adding closed-domain skills
                skills_for_uttr += turn_on_skills(
                    detected_topics,
                    intent_catcher_intents,
                    user_uttr_text,
                    bot_uttr.get("text", ""),
                    available_skills=[
                        "news_api_skill",
                        "dff_coronavirus_skill",
                        "dff_funfact_skill",
                        "dff_weather_skill",
                        "dff_short_story_skill",
                    ],
                )
                # adding linked-to skills
                skills_for_uttr.extend(get_linked_to_skills(dialog))
                skills_for_uttr.extend(get_previously_active_skill(dialog))
            else:
                # general case
                if low_priority_intent_detected:
                    skills_for_uttr.append("dff_intent_responder_skill")
                    skills_for_uttr.append("robot_skill")
                # adding open-domain skills
                skills_for_uttr.append("dff_grounding_skill")
                skills_for_uttr.append("dff_program_y_skill")
                skills_for_uttr.append("personal_info_skill")
                skills_for_uttr.append("meta_script_skill")
                skills_for_uttr.append("dummy_skill")
                skills_for_uttr.append("dialogpt")  # generative skill
                skills_for_uttr.append("dialogpt_persona_based")  # generative skill persona-based
                skills_for_uttr.append("small_talk_skill")
                skills_for_uttr.append("knowledge_grounding_skill")
                skills_for_uttr.append("convert_reddit")
                skills_for_uttr.append("comet_dialog_skill")
                skills_for_uttr.append("dff_program_y_wide_skill")
                # we have only russian version of dff_generative_skill
                skills_for_uttr.append("dff_generative_skill")
                skills_for_uttr.append("gpt2-generator")

                # adding friendship only in the beginning of the dialog
                if len(dialog["utterances"]) < 20:
                    skills_for_uttr.append("dff_friendship_skill")

                if if_choose_topic_detected or if_lets_chat_about_particular_topic_detected:
                    skills_for_uttr.append("knowledge_grounding_skill")
                    skills_for_uttr.append("news_api_skill")

                switch_wiki_skill, _ = if_switch_wiki_skill(user_uttr, bot_uttr)
                if switch_wiki_skill or switch_wiki_skill_on_news(user_uttr, bot_uttr):
                    skills_for_uttr.append("dff_wiki_skill")
                if if_switch_test_skill(user_uttr, bot_uttr):
                    skills_for_uttr.append("dff_art_skill")

                # adding factoidQA Skill if user utterance is factoid question
                if is_factoid:
                    skills_for_uttr.append("factoid_qa")

                if "dummy_skill" in prev_active_skill and len(dialog["utterances"]) > 4:
                    skills_for_uttr.append("dummy_skill_dialog")

                # if user mentions
                if is_celebrity_mentioned:
                    skills_for_uttr.append("dff_gossip_skill")
                # some special cases
                if if_special_weather_turn_on(user_uttr, bot_uttr):
                    skills_for_uttr.append("dff_weather_skill")
                if if_turn_on_emotion(user_uttr, bot_uttr):
                    skills_for_uttr.append("emotion_skill")
                if get_named_locations(user_uttr):
                    skills_for_uttr.append("dff_travel_skill")
                if extract_movies_names_from_annotations(user_uttr):
                    skills_for_uttr.append("dff_movie_skill")

                # adding closed-domain skills
                skills_for_uttr += turn_on_skills(
                    detected_topics,
                    intent_catcher_intents,
                    user_uttr_text,
                    bot_uttr.get("text", ""),
                    available_skills=[
                        "dff_art_skill",
                        "dff_movie_skill",
                        "dff_book_skill",
                        "news_api_skill",
                        "dff_food_skill",
                        "dff_animals_skill",
                        "dff_sport_skill",
                        "dff_music_skill",
                        "dff_science_skill",
                        "dff_gossip_skill",
                        "game_cooperative_skill",
                        "dff_weather_skill",
                        "dff_funfact_skill",
                        "dff_travel_skill",
                        "dff_coronavirus_skill",
                        "dff_bot_persona_skill",
                        "dff_gaming_skill",
                        "dff_short_story_skill",
                    ],
                )
                # adding linked-to skills
                skills_for_uttr.extend(get_linked_to_skills(dialog))
                skills_for_uttr.extend(get_previously_active_skill(dialog))

            # NOW IT IS NOT ONLY FOR USUAL CONVERSATION BUT ALSO FOR SENSITIVE/HIGH PRIORITY INTENTS/ETC

            if "dff_coronavirus_skill" in skills_for_uttr:
                #  no convert & comet when about coronavirus
                if "convert_reddit" in skills_for_uttr:
                    skills_for_uttr.remove("convert_reddit")
                if "comet_dialog_skill" in skills_for_uttr:
                    skills_for_uttr.remove("comet_dialog_skill")

            if len(dialog["utterances"]) > 1:
                # Use only misheard asr skill if asr is not confident and skip it for greeting
                if user_uttr_annotations.get("asr", {}).get("asr_confidence", "high") == "very_low":
                    skills_for_uttr = ["misheard_asr"]

            if "/alexa_" in user_uttr.get("orig_text", user_uttr_text):
                # adding alexa handler for Amazon Alexa specific commands
                skills_for_uttr = ["alexa_handler"]

            if "tell_me_a_story" in intent_catcher_intents:
                skills_for_uttr.append("dff_short_story_skill")

            if len(dialog["human_utterances"]) > 1:
                nouns = dialog["human_utterances"][-1].get("annotations", {}).get("rake_keywords", [])
                nouns.extend(dialog["human_utterances"][-2].get("annotations", {}).get("rake_keywords", []))
                if prev_active_skill != "dff_short_story_skill":
                    if len(nouns) >= 5:
                        skills_for_uttr.append("dff_short_story_skill")

            logger.info(f"Selected skills: {skills_for_uttr}")
            total_time = time.time() - st_time
            logger.info(f"rule_based_selector exec time = {total_time:.3f}s")
            asyncio.create_task(callback(task_id=payload["task_id"], response=list(set(skills_for_uttr))))
        except Exception as e:
            total_time = time.time() - st_time
            logger.info(f"rule_based_selector exec time = {total_time:.3f}s")
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=["dff_program_y_skill", "dummy_skill"]))
