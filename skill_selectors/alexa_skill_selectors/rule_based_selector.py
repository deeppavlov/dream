from typing import List, Tuple

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component


@register('rule_based_selector')
class RuleBasedSelector(Component):
    """
    Rule-based skill selector which choosing among TransferTransfo, Base AIML and Alice AIML.
    Rule: if AIML skill matches, turn it on, otherwise TransferTransfo
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self,
                 user_utterances: List[str],
                 aiml_responses_batch: List[str] = None,  # aiml_skill
                 aiml_alice_responses_batch: List[str] = None,  # alice
                 aiml_chitchat_responses_batch: List[str] = None,  # chitchat
                 ) -> List[str]:
        skill_names = []

        for i in range(len(user_utterances)):
            skills_for_uttr = []
            if "aiml" in user_utterances[i]:
                skills_for_uttr.append("aiml")
            if "alice" in user_utterances[i]:
                skills_for_uttr.append("alice")
            skill_names.append(skills_for_uttr)

        return skill_names
