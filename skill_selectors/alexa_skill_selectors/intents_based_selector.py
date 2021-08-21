# TODO: Do not change this file, it does not use
from typing import List, Tuple

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
import logging
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO: THIS SKILL SELECTOR IS NOT WORKING NOW!
#       USE rule_based_selector.py
@register("intents_based_selector")
class RuleBasedSelector(Component):
    """
    Rule-based on intents skill selector which choosing among Alice, AIML, CoBotQA and future chit-chat TransferTransfo
    """

    wh_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how"}

    def __init__(self, **kwargs):
        logger.info("Skill selector Initialized")
        pass

    def __call__(self, states_batch, **kwargs) -> List[List[str]]:

        skill_names = []

        for dialog in states_batch:
            skills_for_uttr = []

            tokens = dialog["utterances"][-1]["text"].lower().split()

            if len(set(tokens).intersection(self.wh_words)) > 0:
                skills_for_uttr.append("aiml")
                skills_for_uttr.append("alice")
                skills_for_uttr.append("cobotqa")
                skills_for_uttr.append("transfertransfo")
            else:
                skills_for_uttr.append("alice")
                skills_for_uttr.append("cobotqa")

            skill_names.append(skills_for_uttr)

        return skill_names
