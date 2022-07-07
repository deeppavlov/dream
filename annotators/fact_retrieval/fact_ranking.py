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
import os
import re
import time
from typing import List

import sentry_sdk
from nltk import sent_tokenize

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

PROHIBITED_WORDS = re.compile(r"(Image|File|\|)", re.IGNORECASE)


@register("fact_ranking_infer")
class FactRankerInfer(Component):
    """Class for ranking of paths in subgraph"""

    def __init__(
        self,
        ranker=None,
        batch_size: int = 64,
        facts_to_leave: int = 3,
        thres=0.94,
        use_topical_chat_facts=True,
        **kwargs,
    ):
        """

        Args:
            load_path: path to folder with wikidata files
            rel_q2name_filename: name of file which maps relation id to name
            ranker: component deeppavlov.models.ranking.rel_ranker
            bert_perprocessor: component deeppavlov.models.preprocessors.bert_preprocessor
            batch_size: infering batch size
            **kwargs:
        """
        self.ranker = ranker
        self.batch_size = batch_size
        self.facts_to_leave = facts_to_leave
        self.thres = thres
        self.use_topical_chat_facts = use_topical_chat_facts

    def __call__(
        self,
        dialog_history_list: List[str],
        first_paragraphs_batch: List[List[str]],
        topical_chat_facts_batch: List[List[str]] = None,
        sentences_batch: List[List[str]] = None,
    ) -> List[List[str]]:
        top_facts_batch = []
        if sentences_batch is None:
            sentences_batch = [[] for _ in dialog_history_list]
        if topical_chat_facts_batch is None:
            topical_chat_facts_batch = [[] for _ in dialog_history_list]
        tm1 = time.time()
        for dialog_history, sentences_list, topical_chat_facts, first_paragraphs_list in zip(
            dialog_history_list, sentences_batch, topical_chat_facts_batch, first_paragraphs_batch
        ):
            first_par_list = []
            cand_facts = []
            if sentences_list:
                cand_facts = sentences_list
            for first_paragraphs in first_paragraphs_list:
                for paragraph in first_paragraphs:
                    sentences = sent_tokenize(paragraph)
                    first_par_list += sentences[:2]
            if self.use_topical_chat_facts and topical_chat_facts:
                for paragraph in topical_chat_facts:
                    sentences = sent_tokenize(paragraph)
                    cand_facts.extend([sentence for sentence in sentences if len(sentence.split()) < 150])

            facts_with_scores = []
            top_facts = []
            if cand_facts:
                n_batches = len(cand_facts) // self.batch_size + int(len(cand_facts) % self.batch_size > 0)
                logger.info(f"num batches {n_batches}")
                for i in range(n_batches):
                    dh_batch = []
                    facts_batch = []
                    for candidate_fact in cand_facts[i * self.batch_size : (i + 1) * self.batch_size]:
                        dh_batch.append(dialog_history)
                        facts_batch.append(candidate_fact)

                    if dh_batch:
                        probas = self.ranker(dh_batch, facts_batch)
                        probas = [proba[1] for proba in probas]
                        for j, fact in enumerate(facts_batch):
                            facts_with_scores.append((fact, probas[j]))

                facts_with_scores = sorted(facts_with_scores, key=lambda x: x[1], reverse=True)
                top_facts = [fact for fact, score in facts_with_scores if score > self.thres]
            top_facts = first_par_list + top_facts
            top_facts = [fact for fact in top_facts if not re.findall(PROHIBITED_WORDS, fact)]
            top_facts_batch.append(top_facts[: self.facts_to_leave])
        tm2 = time.time()
        logger.info(f"time of ranking {tm2 - tm1}")

        return top_facts_batch
