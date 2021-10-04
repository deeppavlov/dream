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
from typing import Union, Dict, List
from enum import Enum
import collections
import copy

import sentry_sdk
from emora_stdm import DialogueFlow, NatexNLG, Macro, NatexNLU, KnowledgeBase

import common.dialogflow_framework.stdm.utils as utils
from common.dialogflow_framework.programy.model import MindfulDataFileBot

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


class DFEasyFilling:
    def __init__(
        self,
        initial_state: Union[Enum, str, tuple] = "",
        initial_speaker=DialogueFlow.Speaker.USER,
        macros: Dict[str, Macro] = None,
        kb: Union[KnowledgeBase, str, List[str]] = None,
        default_system_state=None,
        end_state="__end__",
        all_multi_hop=True,
        wordnet=False,
        dialogflow=None,
    ):
        if dialogflow:
            self.df = dialogflow
        else:
            assert initial_state
            self.df = DialogueFlow(
                initial_state,
                initial_speaker,
                macros,
                kb,
                default_system_state,
                end_state,
                all_multi_hop,
                wordnet,
            )
        self.local_user_transitions = collections.defaultdict(dict)
        self.global_user_transitions = {}
        self.error_transitions = {}
        self.states = set()
        if initial_state:
            self._add_states(initial_state)

    def get_dialogflow(self):
        df_backup = copy.deepcopy(self.df)
        self._compile_dialogflow()
        result_df = self.df
        self.df = df_backup
        return result_df

    def add_global_user_transition(self, state_to, intent, importance=1.0):
        if not utils.check_intent(intent):
            raise Exception("Unknown intent type")
        elif state_to in self.global_user_transitions:
            raise Exception(f"{state_to} is already defined")
        else:
            self._add_states(state_to)
            self.global_user_transitions[state_to] = {"intent": intent, "importance": importance}

    def add_user_transition(self, state_from, state_to, intent, importance=1.0):
        if not utils.check_intent(intent):
            raise Exception("Unknown intent type")
        elif state_to in self.local_user_transitions[state_from]:
            raise Exception(f"{state_to} is already defined")
        else:
            self._add_states(state_from, state_to)
            self.local_user_transitions[state_from][state_to] = {"intent": intent, "importance": importance}

    def add_system_transition(self, state_from, state_to, nlg):
        self._add_states(state_from, state_to)
        if isinstance(nlg, (str, NatexNLG)):
            self.df.add_system_transition(state_from, state_to, nlg)

        elif isinstance(nlg, (set, list)):
            nlg = utils.strs2natex_nlg(nlg)
            self.df.add_system_transition(state_from, state_to, nlg)

        elif callable(nlg):  # nlg(vars=vars) -> str

            class NLGMacro(Macro):
                def run(self, ngrams, vars, args):
                    try:
                        text = nlg(vars=vars)
                        text = utils.clean_text(text)
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
        # self._add_states(state_from, state_to)
        # self.df.set_error_successor(state_from, state_to)
        self.error_transitions[state_from] = state_to
        pass

    def add_user_serial_transitions(self, state_from, states_to, default_importance=1.0):
        # order in states_to is important
        for state_to, condition in states_to.items():
            intent, importance = (
                (condition[0], condition[1])
                if isinstance(condition, (list, tuple))
                else (condition, default_importance)
            )
            self.add_user_transition(
                state_from,
                state_to,
                intent,
                importance,
            )

    def add_global_user_serial_transitions(self, states_to, default_importance=1.0):
        # order in states_to is important
        for state_to, condition in states_to.items():
            intent, importance = (
                (condition[0], condition[1])
                if isinstance(condition, (list, tuple))
                else (condition, default_importance)
            )
            self.add_global_user_transition(
                state_to,
                intent,
                importance,
            )

    def _add_user_transitions(self, state_from, states_to):
        # order in states_to is important
        condition_sequence = []
        for state_to, condition in states_to.items():
            condition_sequence += [condition]
            self._add_user_transition(
                state_from,
                state_to,
                utils.create_intent_sequence(condition_sequence[:-1], condition_sequence[-1:]),
            )

    def _add_user_transition(self, state_from, state_to, intent):
        if isinstance(intent, (str, NatexNLU)):
            self.df.add_user_transition(state_from, state_to, intent)

        elif isinstance(intent, (set, list)):
            intent = utils.disjunction_natex_nlu_strs(intent)
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

    def _compile_dialogflow(self):
        transitions = {state_from: copy.deepcopy(self.global_user_transitions) for state_from in self._get_usr_states()}
        logger.debug(f"transitions={transitions}")
        logger.debug(f"self.states={self.states}")
        logger.debug(f"self.local_user_transitions={self.local_user_transitions}")
        logger.debug(f"self._get_usr_states()={self._get_usr_states()}")

        for state_from in transitions:
            user_transition_from = transitions[state_from]
            user_transition_from.update(self.local_user_transitions.get(state_from, {}))
            ordered_states_to = sorted(
                user_transition_from,
                key=lambda state_to: -user_transition_from[state_to].get("importance", 1.0),
            )
            state_to2intent = {state_to: user_transition_from[state_to]["intent"] for state_to in ordered_states_to}
            self._add_user_transitions(state_from, state_to2intent)

        for state_from, state_to in self.error_transitions.items():
            self.df.set_error_successor(state_from, state_to)

    def _add_states(self, *args):
        for state in args:
            text_state = str(state[1]) if isinstance(state, (tuple, list)) else str(state)
            text_prefix = "State."
            prefix_len = len(text_prefix)
            if not (text_prefix == text_state[:prefix_len]):
                raise Exception(f"state {state} has to be from State class")
            if not (
                text_state[prefix_len : prefix_len + 3]
                in [
                    "SYS",
                    "USR",
                ]
            ):
                raise Exception(f"state {state} has to contain SYS or USR in of the begining")
            self.states.add(state)

    def _get_usr_states(self):
        text_prefix = "State.USR"
        prefix_len = len(text_prefix)
        sys_states = []
        for state in self.states:
            text_state = str(state[1]) if isinstance(state, (tuple, list)) else str(state)
            if text_state[:prefix_len] == text_prefix:
                sys_states.append(state)
        return sys_states
