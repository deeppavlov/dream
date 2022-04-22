import random
from typing import List, Union


class FAQResponseGenerator:
    """
    Class provides a random response for a FAQ task having a mapping:
    ```json
    {
        "response_0": ["Hi! This is a Dream Socialbot!"],
        "response_1": ["I'm great!", "I'm good. How are you?"]
    }
    ```
    for a particular class (of classes).
    If no class label is provided, returns empty response.
    """
    def __init__(self, responses_map, return_list=False, *args, **kwargs):
        self.responses_map = responses_map
        self.return_list = return_list

    def __call__(self, x: List[str], *args, **kwargs) -> Union[str, List[str]]:
        if len(x) > 0:
            all_responses_ro_consider = sum([self.responses_map[pred_class] for pred_class in x], [])

            if self.return_list:
                return all_responses_ro_consider
            else:
                return random.choice(all_responses_ro_consider)
        else:
            if self.return_list:
                return []
            else:
                return ""
