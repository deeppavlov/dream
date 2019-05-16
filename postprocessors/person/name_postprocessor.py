# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
from typing import List
from logging import getLogger

from deeppavlov.core.models.component import Component

logger = getLogger()


class NameAskerPostprocessor(Component):

    def __init__(self,
                 state_slot: str = 'user_name',
                 flag_slot: str = 'asked_name',
                 **kwargs) -> None:
        self.state_slot = state_slot
        self.flag_slot = flag_slot

    def __call__(self,
                 utters: List[str],
                 histories: List[List[str]],
                 states: List[dict],
                 responses: List[str],
                 **kwargs) -> List[str]:
        new_responses, new_states = [], []
        states = states if states else [{}] * len(utters)
        for utter, hist, state, resp in zip(utters, histories, states, responses):
            state = state or {}
            if (self.state_slot not in state) and (self.flag_slot not in state):
                if (len(hist) == 0) and (random.random() < 0.2):
                    new_responses.append('Привет! Тебя как зовут?')
                    state[self.flag_slot] = True
                elif (len(hist) < 5) and (random.random() < 0.5):
                    new_responses.append('Как тебя зовут?')
                    state[self.flag_slot] = True
                elif (len(hist) >= 5) and (random.random() < 0.1):
                    new_responses.append('Тебя как зовут-то?')
                    state[self.flag_slot] = True
                else:
                    new_responses.append(resp)
            else:
                new_responses.append(resp)
            new_states.append(state)
        return new_responses, new_states
