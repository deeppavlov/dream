from typing import List, Tuple

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component


@register('rule_based_selector')
class RuleBasedSelector(Component):
    """
    Rule-based skill selector which choosing among TrnasferTransfo, Base AIML and Alice AIML.
    Rule: if AIML skill matches, turn it on, otherwise TrnasferTransfo
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self,
                 user_replies_batch: List[str],
                 aiml_alice_responses_batch: List[Tuple[str, float]] = None,  # alice
                 aiml_responses_batch: List[Tuple[str, float]] = None,  # aiml_skill
                 aiml_chitchat_responses_batch: List[Tuple[str, float]] = None,  # chitchat
                 aiml_alice_null_response: str = "",
                 aiml_null_response: str = "I don't know",
                 ) -> List[str]:

        skill_names = []

        for i in range(len(user_replies_batch)):
            if aiml_alice_responses_batch and aiml_alice_responses_batch[i][0] != aiml_alice_null_response:
                skill_names.append("alice")
            elif aiml_responses_batch and aiml_responses_batch[i][0] != aiml_null_response:
                skill_names.append("aiml_skill")
            elif aiml_chitchat_responses_batch:
                skill_names.append("chitchat")
            else:
                skill_names.append("")

        return skill_names
