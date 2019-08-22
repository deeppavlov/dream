from typing import List, Tuple

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component


@register('rule_based_selector')
class RuleBasedSelector(Component):
    """
    Rule-based skill selector which choosing among TransferTransfo, Base AIML and Alice AIML.
    Rule: if AIML skill matches, turn it on, otherwise TransferTransfo
    """

    def __init__(self,
                 aiml_null_response: str = "I don't know",
                 aiml_alice_null_response: str = "",
                 **kwargs):
        self.aiml_null_response = aiml_null_response
        self.aiml_alice_null_response = aiml_alice_null_response

    def __call__(self,
                 user_replies_batch: List[str],
                 aiml_responses_batch: List[str] = None,  # aiml_skill
                 aiml_alice_responses_batch: List[str] = None,  # alice
                 aiml_chitchat_responses_batch: List[str] = None,  # chitchat
                 ) -> List[str]:
        best_answers = []

        for i in range(len(user_replies_batch)):
            if aiml_alice_responses_batch and aiml_alice_responses_batch[i][0] != self.aiml_alice_null_response:
                best_answers.append(aiml_alice_responses_batch[i][0])
            elif aiml_responses_batch and aiml_responses_batch[i][0] != self.aiml_null_response:
                best_answers.append(aiml_responses_batch[i][0])
            elif aiml_chitchat_responses_batch:
                best_answers.append(aiml_chitchat_responses_batch[i][0])
            else:
                best_answers.append("")

        return best_answers
