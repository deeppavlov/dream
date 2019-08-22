from typing import List, Tuple

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component


@register('rule_based_selector')
class RuleBasedSelector(Component):
    """
    Rule-based skill selector which choosing among TransferTransfo, Base AIML and Alice AIML
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self,
                 utterances_batch: List[str],
                 history_batch,
                 states_batch
                 ) -> List[List[str]]:

        skill_names = []

        for i in range(len(utterances_batch)):
            skills_for_uttr = []
            if "aiml" in utterances_batch[i]:
                skills_for_uttr.append("aiml")
            if "alice" in utterances_batch[i]:
                skills_for_uttr.append("alice")
            skill_names.append(skills_for_uttr)

        return skill_names
