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

from collections import defaultdict
from logging import getLogger
from typing import List

import numpy as np
from nltk.corpus import stopwords

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

log = getLogger(__name__)


@register("question_sign_checker")
class QuestionSignChecker(Component):
    """This class adds question sign if it is absent or replaces dot with question sign"""

    def __init__(self, **kwargs):
        pass

    def __call__(self, questions: List[str]) -> List[str]:
        questions_sanitized = []
        for question in questions:
            if not question.endswith("?"):
                if question.endswith("."):
                    question = question[:-1] + "?"
                else:
                    question += "?"
            questions_sanitized.append(question)
        return questions_sanitized


@register("entity_detection_parser")
class EntityDetectionParser(Component):
    """This class parses probabilities of tokens to be a token from the entity substring."""

    def __init__(
        self,
        o_tag: str,
        tags_file: str,
        entity_tags: List[str] = None,
        return_entities_with_tags: bool = False,
        add_nouns: bool = False,
        thres_proba: float = 0.95,
        misc_proba: float = 0.7,
        **kwargs
    ):
        self.entity_tags = entity_tags
        self.o_tag = o_tag
        self.return_entities_with_tags = return_entities_with_tags
        self.thres_proba = thres_proba
        self.misc_proba = misc_proba
        self.tag_ind_dict = {}
        self.stopwords = set(stopwords.words("english"))
        with open(str(expand_path(tags_file))) as fl:
            tags = [line.split("\t")[0] for line in fl.readlines()]
            self.tags = tags
            if add_nouns:
                tags.append("B-MISC")
            if self.entity_tags is None:
                self.entity_tags = list(
                    {tag.split("-")[1] for tag in tags if len(tag.split("-")) > 1}.difference({self.o_tag})
                )

            self.entity_prob_ind = {
                entity_tag: [i for i, tag in enumerate(tags) if entity_tag in tag] for entity_tag in self.entity_tags
            }
            self.tags_ind = {tag: i for i, tag in enumerate(tags)}
            self.et_prob_ind = [i for tag, ind in self.entity_prob_ind.items() for i in ind]
            for entity_tag, tag_ind in self.entity_prob_ind.items():
                for ind in tag_ind:
                    self.tag_ind_dict[ind] = entity_tag
            self.tag_ind_dict[0] = self.o_tag

    def __call__(
        self,
        text_batch: List[str],
        tokens_batch: List[List[str]],
        tags_batch: List[List[List[float]]],
        tokens_probas_batch: np.ndarray,
    ):
        entities_batch, positions_batch, probas_batch, tokens_conf_batch, new_tags_batch = [], [], [], [], []
        for tokens, probas in zip(tokens_batch, tokens_probas_batch):
            new_tags, new_tag_probas = self.tags_from_probas(tokens, probas)
            new_tags_batch.append(new_tags)

        res_tags_batch = []
        for tokens_list, tags_list, new_tags_list in zip(tokens_batch, tags_batch, new_tags_batch):
            res_tags_list = []
            for token, tag, new_tag in zip(tokens_list, tags_list, new_tags_list):
                if tag == "O" and new_tag != "O" and token.lower() not in self.stopwords:
                    res_tags_list.append(new_tag)
                else:
                    res_tags_list.append(tag)
            res_tags_batch.append(res_tags_list)

        for probas in tokens_probas_batch:
            tokens_conf = [round(1.0 - proba[0], 4) for proba in probas]
            tokens_conf_batch.append(tokens_conf)
        for text, tokens, res_tags, probas in zip(text_batch, tokens_batch, res_tags_batch, tokens_probas_batch):
            entities, positions, entities_probas = self.entities_from_tags(text, tokens, res_tags, probas)
            entities_batch.append(entities)
            positions_batch.append(positions)
            probas_batch.append(entities_probas)
        return entities_batch, positions_batch, probas_batch, tokens_conf_batch

    def tags_from_probas(self, tokens, probas):
        tags = []
        tag_probas = []
        for proba in probas:
            if proba[0] < self.thres_proba:
                tag_num = np.argmax(proba[1:]) + 1
            else:
                tag_num = 0
            tags.append(self.tags[tag_num])
            tag_probas.append(proba[tag_num])

        return tags, tag_probas

    def entities_from_tags(self, text, tokens, tags, tag_probas):
        """
        This method makes lists of substrings corresponding to entities and entity types
        and a list of indices of tokens which correspond to entities

        Args:
            tokens: list of tokens of the text
            tags: list of tags for tokens
            tag_probas: list of probabilities of tags

        Returns:
            list of entity substrings (or a dict of tags (keys) and entity substrings (values))
            list of substrings for entity types
            list of indices of tokens which correspond to entities (or a dict of tags (keys)
                and list of indices of entity tokens)
        """
        entities_dict = defaultdict(list)
        entity_dict = defaultdict(list)
        entity_positions_dict = defaultdict(list)
        entities_positions_dict = defaultdict(list)
        entities_probas_dict = defaultdict(list)
        entity_probas_dict = defaultdict(list)
        replace_tokens = [("'s", ""), (" .", ""), ("{", ""), ("}", ""), ("  ", " "), ('"', "'"), ("(", ""), (")", "")]

        cnt = 0
        for tok, tag, probas in zip(tokens, tags, tag_probas):
            if tag.split("-")[-1] in self.entity_tags:
                f_tag = tag.split("-")[-1]
                if tag.startswith("B-") and any(entity_dict.values()):
                    for c_tag, entity in entity_dict.items():
                        entity = " ".join(entity)
                        for old, new in replace_tokens:
                            entity = entity.replace(old, new)
                        if entity and entity.lower() not in self.stopwords:
                            entities_dict[c_tag].append(entity)
                            entities_positions_dict[c_tag].append(entity_positions_dict[c_tag])
                            cur_probas = entity_probas_dict[c_tag]
                            entities_probas_dict[c_tag].append(round(sum(cur_probas) / len(cur_probas), 4))
                        entity_dict[c_tag] = []
                        entity_positions_dict[c_tag] = []
                        entity_probas_dict[c_tag] = []

                if tok not in {"?", "!"}:
                    entity_dict[f_tag].append(tok)
                    entity_positions_dict[f_tag].append(cnt)
                    if f_tag == "MISC":
                        entity_probas_dict[f_tag].append(self.misc_proba)
                    else:
                        entity_probas_dict[f_tag].append(probas[self.tags_ind[tag]])

            elif any(entity_dict.values()):
                for tag, entity in entity_dict.items():
                    c_tag = tag.split("-")[-1]
                    entity = " ".join(entity)
                    for old, new in replace_tokens:
                        entity = entity.replace(old, new)
                        if entity.replace(" - ", "-").lower() in text.lower():
                            entity = entity.replace(" - ", "-")
                    if entity and entity.lower() not in self.stopwords:
                        entities_dict[c_tag].append(entity)
                        entities_positions_dict[c_tag].append(entity_positions_dict[c_tag])
                        cur_probas = entity_probas_dict[c_tag]
                        entities_probas_dict[c_tag].append(round(sum(cur_probas) / len(cur_probas), 4))

                    entity_dict[c_tag] = []
                    entity_positions_dict[c_tag] = []
                    entity_probas_dict[c_tag] = []
            cnt += 1

        if any(entity_dict.values()):
            for tag, entity in entity_dict.items():
                c_tag = tag.split("-")[-1]
                entity = " ".join(entity)
                for old, new in replace_tokens:
                    entity = entity.replace(old, new)
                    if entity.replace(" - ", "-").lower() in text.lower():
                        entity = entity.replace(" - ", "-")
                if entity and entity.lower() not in self.stopwords:
                    entities_dict[c_tag].append(entity)
                    entities_positions_dict[c_tag].append(entity_positions_dict[c_tag])
                    cur_probas = entity_probas_dict[c_tag]
                    entities_probas_dict[c_tag].append(round(sum(cur_probas) / len(cur_probas), 4))

        entities_list = [entity for tag, entities in entities_dict.items() for entity in entities]
        entities_positions_list = [
            position for tag, positions in entities_positions_dict.items() for position in positions
        ]
        entities_probas_list = [proba for tag, proba in entities_probas_dict.items() for proba in probas]

        if self.return_entities_with_tags:
            return entities_dict, entities_positions_dict, entities_probas_dict
        else:
            return entities_list, entities_positions_list, entities_probas_list
