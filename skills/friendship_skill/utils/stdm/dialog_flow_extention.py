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

import logging
import uuid
import os

from emora_stdm import DialogueFlow, NatexNLG, Macro, NatexNLU

import utils.stdm.utils as stdm_utils
from utils.programy.model import MindfulDataFileBot
import sentry_sdk

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


class DFEasyFilling:
    def __init__(self, df: DialogueFlow):
        self.df = df
        self.cnt = 0

    def add_user_transition(self, state_from, state_to, intent):
        if isinstance(intent, (str, NatexNLU)):
            self.df.add_user_transition(state_from, state_to, intent)

        elif isinstance(intent, (set, list)):
            intent = stdm_utils.disjunction_natex_nlu_strs(intent)
            self.df.add_user_transition(state_from, state_to, intent)

        elif callable(intent):
            if isinstance(intent, MindfulDataFileBot):  # using programy as intent

                def handler(ngrams, vars):
                    # TODO: n turns
                    return intent([ngrams.text()])

            else:
                handler = intent  # intent(ngrams=ngrams, vars=vars) -> bool

            class IntentMacro(Macro):
                def run(self, ngrams, vars, args):
                    try:
                        is_match = handler(ngrams=ngrams, vars=vars)
                    except Exception as exc:
                        sentry_sdk.capture_exception(exc)
                        logger.exception(exc)
                        is_match = False
                    if is_match:
                        return ngrams.text()
                    else:
                        return ""

            macros_name = uuid.uuid4().hex
            self.df.add_user_transition(
                state_from,
                state_to,
                NatexNLU(
                    f"#{macros_name}()",
                    macros={f"{macros_name}": IntentMacro()},
                ),
            )

        else:
            raise Exception("Unknown intent type")

    def add_system_transition(self, state_from, state_to, nlg):
        if isinstance(nlg, (str, NatexNLG)):
            self.df.add_system_transition(state_from, state_to, nlg)

        elif isinstance(nlg, (set, list)):
            nlg = stdm_utils.strs2natex_nlg(nlg)
            self.df.add_system_transition(state_from, state_to, nlg)

        elif callable(nlg):  # nlg(vars=vars) -> str

            class NLGMacro(Macro):
                def run(self, ngrams, vars, args):
                    try:
                        text = nlg(vars=vars)
                        text = stdm_utils.clean_text(text)
                        return text
                    except Exception as exc:
                        sentry_sdk.capture_exception(exc)
                        logger.exception(exc)
                        return ""

            macros_name = uuid.uuid4().hex

            self.df.add_system_transition(
                state_from,
                state_to,
                NatexNLG(
                    f"#{macros_name}()",
                    macros={f"{macros_name}": NLGMacro()},
                ),
            )

        else:
            raise Exception("Unknown nlg type")

    def set_error_successor(self, state_from, state_to):
        self.df.set_error_successor(state_from, state_to)

    def add_user_serial_transitions(self, state_from, states_to):
        # order in states_to is important
        condition_sequence = []
        for state_to, condition in states_to.items():
            condition_sequence += [condition]
            self.add_user_transition(
                state_from,
                state_to,
                stdm_utils.create_intent_sequence(condition_sequence[:-1], condition_sequence[-1:]),
            )
