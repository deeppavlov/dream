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
import logging

from programy.clients.embed.basic import EmbeddedDataFileBot

from common.dialogflow_framework.programy.text_preprocessing import clean_text

logger = logging.getLogger(__name__)


class MindfulDataFileBot(EmbeddedDataFileBot):
    def ask_question(self, userid, question):
        client_context = self.create_client_context(userid)
        return self.renderer.render(client_context, self.process_question(client_context, question))

    def __call__(self, human_utterances, clean_response=False):
        userid = uuid.uuid4().hex
        for uttr in human_utterances:
            uttr = clean_text(uttr)
            response = self.ask_question(userid, uttr)
        response = response if response else ""
        response = clean_text(response) if clean_response else response
        return response


def get_configuration_files(
    aiml_dirs=None,
    learnf_dirs=None,
    sets_dirs=None,
    maps_dirs=None,
    rdfs_dirs=None,
    conversations_dir=None,
    services_dir=None,
    properties_txt_file=None,
    defaults_txt_file=None,
    denormals_txt_file=None,
    normals_txt_file=None,
    genders_txt_file=None,
    persons_txt_file=None,
    person2s_txt_file=None,
    triggers_txt_file=None,
    regexes_txt_file=None,
    spellings_txt_file=None,
    duplicates_txt_file=None,
    errors_txt_file=None,
    licenses_keys_file=None,
    usergroups_yaml_file=None,
    preprocessors_conf_file=None,
    postprocessors_conf_file=None,
    postquestionprocessors_conf_file=None,
):
    # example:
    # ############# From storage
    # aiml_dirs -> aiml = [".../storage/categories"],
    # learnf_dirs -> learnf = [".../storage/categories/learnf"],
    # sets_dirs -> sets = [".../storage/sets"],
    # maps_dirs -> maps = [".../storage/maps"],
    # rdfs_dirs -> rdfs = [".../storage/rdfs"],
    # conversations_dir -> conversations = ".../storage/conversations",
    # services_dir -> services = ".../storage/services",
    # ############# From properties
    # properties_txt_file -> properties = ".../storage/properties/properties.txt",
    # defaults_txt_file -> defaults = ".../storage/properties/defaults.txt",
    # ############# From lookups
    # denormals_txt_file -> denormals = ".../storage/lookups/denormal.txt",
    # normals_txt_file -> normals = ".../storage/lookups/normal.txt",
    # genders_txt_file -> genders = ".../storage/lookups/gender.txt",
    # persons_txt_file -> persons = ".../storage/lookups/person.txt",
    # person2s_txt_file -> person2s = ".../storage/lookups/person2.txt",
    # ############# From triggers
    # triggers_txt_file -> triggers = ".../storage/triggers/triggers.txt",
    # ############# From regex
    # regexes_txt_file -> regexes = ".../storage/regex/regex-templates.txt",
    # ############# From spelling
    # spellings_txt_file -> spellings = ".../storage/spelling/corpus.txt",
    # ############# From debug
    # duplicates_txt_file -> duplicates = ".../storage/debug/duplicates.txt",
    # errors_txt_file -> errors = ".../storage/debug/errors.txt",
    # ############# From licenses
    # licenses_keys_file -> licenses = ".../storage/licenses/license.keys",
    # ############# From security
    # usergroups_yaml_file -> usergroups = ".../storage/security/usergroups.yaml",
    # ############# From processing
    # preprocessors_conf_file -> preprocessors = ".../storage/processing/preprocessors.conf",
    # postprocessors_conf_file -> postprocessors = ".../storage/processing/postprocessors.conf",
    # postquestionprocessors_conf_file -> postquestionprocessors = ".../storage/processing/postquestionprocessors.conf",
    files = {}
    if aiml_dirs:
        files["aiml"] = aiml_dirs
    if learnf_dirs:
        files["learnf"] = learnf_dirs
    if sets_dirs:
        files["sets"] = sets_dirs
    if maps_dirs:
        files["maps"] = maps_dirs
    if rdfs_dirs:
        files["rdfs"] = rdfs_dirs
    if conversations_dir:
        files["conversations"] = conversations_dir
    if services_dir:
        files["services"] = services_dir
    if properties_txt_file:
        files["properties"] = properties_txt_file
    if defaults_txt_file:
        files["defaults"] = defaults_txt_file
    if denormals_txt_file:
        files["denormals"] = denormals_txt_file
    if normals_txt_file:
        files["normals"] = normals_txt_file
    if genders_txt_file:
        files["genders"] = genders_txt_file
    if persons_txt_file:
        files["persons"] = persons_txt_file
    if person2s_txt_file:
        files["person2s"] = person2s_txt_file
    if triggers_txt_file:
        files["triggers"] = triggers_txt_file
    if regexes_txt_file:
        files["regexes"] = regexes_txt_file
    if spellings_txt_file:
        files["spellings"] = spellings_txt_file
    if duplicates_txt_file:
        files["duplicates"] = duplicates_txt_file
    if errors_txt_file:
        files["errors"] = errors_txt_file
    if licenses_keys_file:
        files["licenses"] = licenses_keys_file
    if usergroups_yaml_file:
        files["usergroups"] = usergroups_yaml_file
    if preprocessors_conf_file:
        files["preprocessors"] = preprocessors_conf_file
    if postprocessors_conf_file:
        files["postprocessors"] = postprocessors_conf_file
    if postquestionprocessors_conf_file:
        files["postquestionprocessors"] = postquestionprocessors_conf_file

    dropped_files = {}
    for name, file in files.items():
        if isinstance(file, list):
            sub_files = [pathlib.Path(sub_file) for sub_file in file]
            sub_files = [sub_file for sub_file in sub_files if not sub_file.exists()]
            if sub_files:
                dropped_files[name] = sub_files
        elif not pathlib.Path(file).exists():
            dropped_files[name] = pathlib.Path(file)
    if dropped_files:
        raise Exception(f"dropped_files={dropped_files} is not empty")
    return files


def get_programy_model(configuration_files):
    model = MindfulDataFileBot(configuration_files)
    return model
