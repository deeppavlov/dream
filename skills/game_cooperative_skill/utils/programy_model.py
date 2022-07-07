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

import uuid

from utils.text_preprocessing import clean_text


def run_models(models, human_utterances):
    userid = uuid.uuid4().hex
    for uttr in human_utterances:
        uttr = clean_text(uttr)
        # print(uttr)
        results = {model_name: model.ask_question(userid, uttr) for model_name, model in models.items()}
        results = {model_name: result for model_name, result in results.items() if result}
    return results


def cmd_postprocessing(model_results, cmd_only=False, model_name_only=False):
    cmds = {model_name: str(cmd).replace(".", "").upper() for model_name, cmd in model_results.items()}
    cmds = {model_name: cmd for model_name, cmd in cmds.items() if cmd}
    cmds = {model_name: cmd.split()[0] for model_name, cmd in cmds.items()}
    if cmd_only:
        cmds = [cmd for cmd in cmds.values()]
    elif model_name_only:
        cmds = [model_name for model_name in cmds.keys()]
    else:
        cmds = {model_name: {cmd: True} for model_name, cmd in cmds.items()}
    return cmds
