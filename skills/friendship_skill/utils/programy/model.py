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

import pathlib
import uuid

from programy.clients.embed.basic import EmbeddedDataFileBot

from utils.programy.text_preprocessing import clean_text


class MindfulDataFileBot(EmbeddedDataFileBot):
    def ask_question(self, userid, question):
        client_context = self.create_client_context(userid)
        return self.renderer.render(client_context, self.process_question(client_context, question))

    def __call__(self, human_utterances):
        userid = uuid.uuid4().hex
        for uttr in human_utterances:
            uttr = clean_text(uttr)
            response = self.ask_question(userid, uttr)
        return clean_text(response) if response else ""


def get_intent_model(intent_dir_or_intent_name):
    intent_dir = pathlib.Path(intent_dir_or_intent_name)
    intent_dir = (
        intent_dir if intent_dir.exists() else pathlib.Path("programy_storage/intents") / intent_dir_or_intent_name
    )
    assert intent_dir.exists(), "Unknown programy a dir path or an intent name"
    share_set_path = pathlib.Path("programy_storage/sets")
    assert share_set_path.exists(), "Unknown programy a dir path for share sets"
    files = {"aiml": [intent_dir], "sets": [share_set_path]}
    model = MindfulDataFileBot(files)
    return model
