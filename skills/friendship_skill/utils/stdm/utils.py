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

import re


space_tmp = re.compile(r"\s+")
prohibited_sings_tmp = re.compile(r"[^a-z0-9!,\.\?!\(\)'\"]", re.IGNORECASE)


def strs2natex_nlg(strs):
    return str(set(strs)).replace("'", '"')


def disjunction_natex_nlu_strs(natex_nlu_strs):
    return "{" + ", ".join(natex_nlu_strs) + "}"


def clean_text(text):
    text = str(text)
    text = prohibited_sings_tmp.sub(" ", text)
    text = space_tmp.sub(" ", text)
    return text.strip()


def create_intent_sequence(negative_cond_sequence, positive_cond_sequence):
    def serial_intent(ngrams, vars):
        for cond in negative_cond_sequence:
            if cond(ngrams, vars):
                return False
        for cond in positive_cond_sequence:
            if cond(ngrams, vars):
                return True
        return False

    return serial_intent
