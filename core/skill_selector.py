from typing import Dict, List

from core.config import SKILL_NAMES_MAP
from core.service import Service


class ChitchatQASelector(Service):

    def __init__(self, rest_caller):
        super().__init__(rest_caller)

    def __call__(self, state: Dict) -> List[List[str]]:
        """
        Select a skill.
        Args:
            state:

        Returns: a list of skill names for each utterance

        """
        response = self.rest_caller(payload=state)
        # TODO refactor riseapi so it would not return keys from dp config?
        predicted_names = [el[self.rest_caller.names[0]]['skill_names'] for el in response]
        skill_names = [SKILL_NAMES_MAP[name] for name in predicted_names]
        return skill_names
