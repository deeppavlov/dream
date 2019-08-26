from typing import List, Tuple

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


@register('rule_based_selector')
class RuleBasedSelector(Component):
    """
    Rule-based skill selector which choosing among TransferTransfo, Base AIML and Alice AIML
    """
    wh_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how"}

    def __init__(self, **kwargs):
        logger.info("Skill selector Initialized")
        pass

    def __call__(self, states_batch, **kwargs) -> List[List[str]]:

        skill_names = [["aiml", "alice", "cobotqa"] for _ in states_batch]

        for dialog in states_batch:
            skills_for_uttr = []

            tokens = dialog['utterances'][-1]['text'].lower().split()

            if len(set(tokens).intersection(self.wh_words)) > 0:
                skills_for_uttr.append("aiml")
                skills_for_uttr.append("alice")
                skills_for_uttr.append("cobotqa")
            else:
                skills_for_uttr.append("alice")
                skills_for_uttr.append("cobotqa")

            skill_names.append(skills_for_uttr)

        return skill_names
