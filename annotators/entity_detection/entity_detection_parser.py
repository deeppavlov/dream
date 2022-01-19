import logging
from typing import List, Tuple
from collections import defaultdict

import numpy as np

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@register("entity_detection_parser")
class EntityDetectionParser(Component):
    """This class parses probabilities of tokens to be a token from the entity substring."""

    def __init__(
        self,
        o_tag: str,
        tags_file: str,
        entity_tags: List[str] = None,
        ignore_points: bool = False,
        return_entities_with_tags: bool = False,
        thres_proba: float = 0.8,
        **kwargs
    ):
        """

        Args:
            entity_tags: tags for entities
            type_tag: tag for types
            o_tag: tag for tokens which are neither entities nor types
            tags_file: filename with NER tags
            ignore_points: whether to consider points as separate symbols
            return_entities_with_tags: whether to return a dict of tags (keys) and list of entity substrings (values)
                or simply a list of entity substrings
            thres_proba: if the probability of the tag is less than thres_proba, we assign the tag as 'O'
        """
        self.entity_tags = entity_tags
        self.o_tag = o_tag
        self.ignore_points = ignore_points
        self.return_entities_with_tags = return_entities_with_tags
        self.thres_proba = thres_proba
        self.tag_ind_dict = {}
        with open(str(expand_path(tags_file))) as fl:
            tags = [line.split("\t")[0] for line in fl.readlines()]
            if self.entity_tags is None:
                if all([(tag.startswith("B-") or tag.startswith("I-") or tag == "O") for tag in tags]):
                    self.entity_tags = list(
                        {tag.split("-")[1] for tag in tags if len(tag.split("-")) > 1}.difference({self.o_tag})
                    )
                else:
                    self.entity_tags = list(
                        {tag.split("-")[0] for tag in tags if len(tag.split("-")) > 1}.difference({self.o_tag})
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
        question_tokens_batch: List[List[str]],
        tokens_offsets_batch: List[List[List[float]]],
        tokens_info_batch: List[List[List[float]]],
        tokens_probas_batch: np.ndarray,
    ) -> Tuple[List[List[str]], List[List[str]], List[List[List[int]]], List[List[List[int]]], List[List[List[float]]]]:
        """

        Args:
            question_tokens: tokenized questions
            token_probas: list of probabilities of question tokens
        Returns:
            Batch of dicts where keys are tags and values are substrings corresponding to tags
            Batch of substrings which correspond to entity types
            Batch of lists of token indices in the text which correspond to entities
        """
        entities_batch = []
        tags_batch = []
        positions_batch = []
        entities_offsets_batch = []
        probas_batch = []
        for tokens, tokens_offsets, tokens_info, probas in zip(
            question_tokens_batch, tokens_offsets_batch, tokens_info_batch, tokens_probas_batch
        ):
            entities, tags, positions, entities_probas = self.entities_from_tags(tokens, tokens_info, probas)
            entities_batch.append(entities)
            tags_batch.append(tags)
            positions_batch.append(positions)
            probas_batch.append(entities_probas)
            entities_offsets = []
            for position in positions:
                start_offset = tokens_offsets[position[0]][0]
                end_offset = tokens_offsets[position[-1]][1]
                entities_offsets.append((start_offset, end_offset))
            entities_offsets_batch.append(entities_offsets)
        return entities_batch, tags_batch, positions_batch, entities_offsets_batch, probas_batch

    def tags_from_probas(self, tokens, probas):
        """
        This method makes a list of tags from a list of probas for tags

        Args:
            probas: probabilities for tokens to belong to particular tags

        Returns:
            list of tags for tokens
            list of probabilities of these tags
        """
        tags = []
        tag_probas = []
        for proba in probas:
            tag_num = np.argmax(proba)
            if tag_num in self.et_prob_ind:
                if proba[tag_num] < self.thres_proba:
                    tag_num = 0
            else:
                tag_num = 0
            tags.append(self.tag_ind_dict[tag_num])
            tag_probas.append(proba[tag_num])

        return tags, tag_probas

    def entities_from_tags(self, tokens, tags, tag_probas):
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
        replace_tokens = [(" - ", "-"), (" .", ""), ("{", ""), ("}", ""), ("  ", " "), ('"', "'"), ("(", ""), (")", "")]

        cnt = 0
        for tok, tag, probas in zip(tokens, tags, tag_probas):
            if (tag.split("-")[0] in {"B", "I"} and tag.split("-")[-1] in self.entity_tags) or (
                tag.split("-")[0] not in {"B", "I"} and tag.split("-")[0] in self.entity_tags
            ):
                if tag.split("-")[0] in {"B", "I"}:
                    f_tag = tag.split("-")[-1]
                else:
                    f_tag = tag.split("-")[0]
                if tag.startswith("B-") and any(entity_dict.values()):
                    for c_tag, entity in entity_dict.items():
                        entity = " ".join(entity)
                        for old, new in replace_tokens:
                            entity = entity.replace(old, new)
                        if entity:
                            entities_dict[c_tag].append(entity)
                            entities_positions_dict[c_tag].append(entity_positions_dict[c_tag])
                            cur_probas = entity_probas_dict[c_tag]
                            entities_probas_dict[c_tag].append(round(sum(cur_probas) / len(cur_probas), 4))
                        entity_dict[c_tag] = []
                        entity_positions_dict[c_tag] = []
                        entity_probas_dict[c_tag] = []

                entity_dict[f_tag].append(tok)
                entity_positions_dict[f_tag].append(cnt)
                entity_probas_dict[f_tag].append(probas[self.tags_ind[tag]])

            elif any(entity_dict.values()):
                for tag, entity in entity_dict.items():
                    if tag.split("-")[0] in {"B", "I"}:
                        c_tag = tag.split("-")[-1]
                    else:
                        c_tag = tag.split("-")[0]
                    entity = " ".join(entity)
                    for old, new in replace_tokens:
                        entity = entity.replace(old, new)
                    if entity:
                        entities_dict[c_tag].append(entity)
                        entities_positions_dict[c_tag].append(entity_positions_dict[c_tag])
                        cur_probas = entity_probas_dict[c_tag]
                        entities_probas_dict[c_tag].append(round(sum(cur_probas) / len(cur_probas), 4))

                    entity_dict[c_tag] = []
                    entity_positions_dict[c_tag] = []
                    entity_probas_dict[c_tag] = []
            cnt += 1

        entities_list = [entity for tag, entities in entities_dict.items() for entity in entities]
        entities_positions_list = [
            position for tag, positions in entities_positions_dict.items() for position in positions
        ]
        entities_probas_list = [proba for tag, proba in entities_probas_dict.items() for proba in probas]
        tags_list = [tag for tag, entities in entities_dict.items() for entity in entities]

        return entities_list, tags_list, entities_positions_list, entities_probas_list
