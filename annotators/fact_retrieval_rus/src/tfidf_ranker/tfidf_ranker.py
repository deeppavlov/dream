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
import time
from logging import getLogger
from typing import List, Any, Tuple

import numpy as np
import pymorphy2

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.estimator import Component
from deeppavlov.models.vectorizers.hashing_tfidf_vectorizer import HashingTfIdfVectorizer

logger = getLogger(__name__)


@register("tfidf_ranker")
class TfidfRanker(Component):
    """Rank documents according to input strings.

    Args:
        vectorizer: a vectorizer class
        top_n: a number of doc ids to return
        active: whether to return a number specified by :attr:`top_n` (``True``) or all ids
         (``False``)

    Attributes:
        top_n: a number of doc ids to return
        vectorizer: an instance of vectorizer class
        active: whether to return a number specified by :attr:`top_n` or all ids
        index2doc: inverted :attr:`doc_index`
        iterator: a dataset iterator used for generating batches while fitting the vectorizer

    """

    def __init__(
        self,
        vectorizer: HashingTfIdfVectorizer,
        top_n=5,
        out_top_n=5,
        active: bool = True,
        filter_flag: bool = False,
        **kwargs,
    ):

        self.top_n = top_n
        self.out_top_n = out_top_n
        self.vectorizer = vectorizer
        self.active = active
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        self.lemmatizer = pymorphy2.MorphAnalyzer()
        self.filter_flag = filter_flag
        self.numbers = 0

    def __call__(
        self, questions: List[str], entity_substr_batch: List[List[str]] = None, tags_batch: List[List[str]] = None
    ) -> Tuple[List[Any], List[float]]:
        """Rank documents and return top n document titles with scores.

        Args:
            questions: list of queries used in ranking

        Returns:
            a tuple of selected doc ids and their scores
        """

        tm_st = time.time()
        batch_doc_ids, batch_docs_scores = [], []

        q_tfidfs = self.vectorizer(questions)
        if entity_substr_batch is None:
            entity_substr_batch = [[] for _ in questions]
            tags_batch = [[] for _ in questions]

        for question, q_tfidf, entity_substr_list, tags_list in zip(
            questions, q_tfidfs, entity_substr_batch, tags_batch
        ):
            if self.filter_flag:
                entity_substr_for_search = []
                if entity_substr_list and not tags_list:
                    tags_list = ["NOUN" for _ in entity_substr_list]
                for entity_substr, tag in zip(entity_substr_list, tags_list):
                    if tag in {"PER", "PERSON", "PRODUCT", "WORK_OF_ART", "COUNTRY", "ORGANIZATION", "NOUN"}:
                        entity_substr_for_search.append(entity_substr)
                if not entity_substr_for_search:
                    for entity_substr, tag in zip(entity_substr_list, tags_list):
                        if tag in {"LOCATION", "LOC", "ORG"}:
                            entity_substr_for_search.append(entity_substr)
                if not entity_substr_for_search:
                    question_tokens = re.findall(self.re_tokenizer, question)
                    for question_token in question_tokens:
                        if self.lemmatizer.parse(question_token)[0].tag.POS == "NOUN" and self.lemmatizer.parse(
                            question_token
                        )[0].normal_form not in {"мир", "земля", "планета", "человек"}:
                            entity_substr_for_search.append(question_token)

                nonzero_scores = set()

                if entity_substr_for_search:
                    ent_tfidf = self.vectorizer([", ".join(entity_substr_for_search)])[0]
                    ent_scores = ent_tfidf * self.vectorizer.tfidf_matrix
                    ent_scores = np.squeeze(ent_scores.toarray())
                    nonzero_scores = set(np.nonzero(ent_scores)[0])

            scores = q_tfidf * self.vectorizer.tfidf_matrix
            scores = np.squeeze(scores.toarray() + 0.0001)  # add a small value to eliminate zero scores

            if self.active:
                thresh = self.top_n
            else:
                thresh = len(self.vectorizer.doc_index)

            if thresh >= len(scores):
                o = np.argpartition(-scores, len(scores) - 1)[0:thresh]
            else:
                o = np.argpartition(-scores, thresh)[0:thresh]
            o_sort = o[np.argsort(-scores[o])]

            filtered_o_sort = []
            if self.filter_flag and nonzero_scores:
                filtered_o_sort = [elem for elem in o_sort if elem in nonzero_scores]
                if filtered_o_sort:
                    filtered_o_sort = np.array(filtered_o_sort)
            if isinstance(filtered_o_sort, list):
                filtered_o_sort = o_sort

            doc_scores = scores[filtered_o_sort].tolist()
            doc_ids = [self.vectorizer.index2doc.get(i, "") for i in filtered_o_sort]

            batch_doc_ids.append(doc_ids[: self.out_top_n])
            batch_docs_scores.append(doc_scores[: self.out_top_n])
        tm_end = time.time()
        logger.info(f"tfidf ranking time: {tm_end - tm_st} num doc_ids {len(batch_doc_ids[0])}")

        return batch_doc_ids, batch_docs_scores
