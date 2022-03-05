import logging
import random
import requests
import sentry_sdk
from os import getenv
from typing import Tuple

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.greeting as common_greeting
import common.link as common_link
from common.constants import MUST_CONTINUE, CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
from common.emotion import is_positive_regexp_based, is_negative_regexp_based
from common.universal_templates import HEALTH_PROBLEMS, COMPILE_SOMETHING
from df_engine.core import Actor, Context


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

REPLY_TYPE = Tuple[str, float, dict, dict, dict]
DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
MIDDLE_CONFIDENCE = 0.95
GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS)



def compose_topic_offering(ctx: Context, actor: Actor, excluded_skills=None) -> str:
    excluded_skills = [] if excluded_skills is None else excluded_skills

    available_skill_names = [
        skill_name for skill_name in link_to_skill2key_words.keys() if skill_name not in excluded_skills
    ]
    if int_ctx.get_age_group(ctx, actor) == "kid":
        available_skill_names = [
            "game_cooperative_skill",
            "dff_animals_skill",
            "dff_food_skill",
            "superheroes",
            "school",
        ]  # for small talk skill
    if len(available_skill_names) == 0:
        available_skill_names = link_to_skill2key_words.keys()

    skill_name = random.choice(available_skill_names)
    if skill_name in link_to_skill2i_like_to_talk:
        response = random.choice(link_to_skill2i_like_to_talk[skill_name])
    else:
        response = f"Would you like to talk about {skill_name}?"
    int_ctx.save_to_shared_memory(ctx, actor, offered_topics=link_to_skill2key_words.get(skill_name, skill_name))

    return response

