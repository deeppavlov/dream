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

from logging import getLogger
from operator import itemgetter
from typing import List, Union, Tuple, Optional

import nltk
from deeppavlov.core.common.chainer import Chainer
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.estimator import Component

logger = getLogger(__name__)


def find_answer_sentence(answer_pos: int, context: str) -> str:
    answer_sentence = ""
    context_sentences = nltk.sent_tokenize(context)
    start = 0
    context_sentences_offsets = []
    for sentence in context_sentences:
        end = start + len(sentence)
        context_sentences_offsets.append((start, end))
        start = end + 1

    for sentence, (start_offset, end_offset) in zip(context_sentences, context_sentences_offsets):
        if start_offset <= answer_pos <= end_offset:
            answer_sentence = sentence
            break

    return answer_sentence


@register("logit_ranker")
class LogitRanker(Component):
    """Select best answer using squad model logits. Make several batches for a single batch, send each batch
    to the squad model separately and get a single best answer for each batch.

    Args:
       squad_model: a loaded squad model
       batch_size: batch size to use with squad model
       sort_noans: whether to downgrade noans tokens in the most possible answers
       top_n: number of answers to return

    Attributes:
       squad_model: a loaded squad model
       batch_size: batch size to use with squad model
       top_n: number of answers to return

    """

    def __init__(
        self,
        squad_model: Union[Chainer, Component],
        batch_size: int = 50,
        sort_noans: bool = False,
        top_n: int = 1,
        return_answer_sentence: bool = False,
        **kwargs,
    ):
        self.squad_model = squad_model
        self.batch_size = batch_size
        self.sort_noans = sort_noans
        self.top_n = top_n
        self.return_answer_sentence = return_answer_sentence

    def __call__(
        self,
        contexts_batch: List[List[str]],
        questions_batch: List[List[str]],
        doc_ids_batch: Optional[List[List[str]]] = None,
    ) -> Union[
        Tuple[List[str], List[float], List[int], List[str]],
        Tuple[List[List[str]], List[List[float]], List[List[int]], List[List[str]]],
        Tuple[List[str], List[float], List[int]],
        Tuple[List[List[str]], List[List[float]], List[List[int]]],
    ]:

        """
        Sort obtained results from squad reader by logits and get the answer with a maximum logit.

        Args:
            contexts_batch: a batch of contexts which should be treated as a single batch in the outer JSON config
            questions_batch: a batch of questions which should be treated as a single batch in the outer JSON config
            doc_ids_batch (optional): names of the documents from which the contexts_batch was derived
        Returns:
             a batch of best answers, their scores, places in contexts
             and doc_ids for this answers if doc_ids_batch were passed
        """
        if doc_ids_batch is None:
            logger.warning(
                "you didn't pass tfidf_doc_ids as input in logit_ranker config so "
                "batch_best_answers_doc_ids can't be compute"
            )

        batch_best_answers = []
        batch_best_answers_score = []
        batch_best_answers_place = []
        batch_best_answers_doc_ids = []
        batch_best_answers_sentences = []
        for quest_ind, [contexts, questions] in enumerate(zip(contexts_batch, questions_batch)):
            results = []
            for i in range(0, len(contexts), self.batch_size):
                c_batch = contexts[i : i + self.batch_size]
                q_batch = questions[i : i + self.batch_size]
                batch_predict = list(zip(*self.squad_model(c_batch, q_batch), c_batch))
                results += batch_predict

            if self.sort_noans:
                results_sort = sorted(results, key=lambda x: (x[0] != "", x[2]), reverse=True)
            else:
                results_sort = sorted(results, key=itemgetter(2), reverse=True)
            best_answers = [x[0] for x in results_sort[: self.top_n]]
            best_answers_place = [x[1] for x in results_sort[: self.top_n]]
            best_answers_score = [x[2] for x in results_sort[: self.top_n]]
            best_answers_contexts = [x[3] for x in results_sort[: self.top_n]]
            batch_best_answers.append(best_answers)
            batch_best_answers_place.append(best_answers_place)
            batch_best_answers_score.append(best_answers_score)
            best_answers_sentences = []

            for answer, place, context in zip(best_answers, best_answers_place, best_answers_contexts):
                sentence = find_answer_sentence(place, context)
                best_answers_sentences.append(sentence)
            batch_best_answers_sentences.append(best_answers_sentences)

            if doc_ids_batch is not None:
                doc_ind = [results.index(x) for x in results_sort]
                batch_best_answers_doc_ids.append(
                    [doc_ids_batch[quest_ind][i] for i in doc_ind][: len(batch_best_answers[-1])]
                )
        logger.info(f"batch_best_answers {batch_best_answers}")
        if self.top_n == 1:
            if batch_best_answers and batch_best_answers[0]:
                batch_best_answers = [x[0] for x in batch_best_answers]
                batch_best_answers_place = [x[0] for x in batch_best_answers_place]
                batch_best_answers_score = [x[0] for x in batch_best_answers_score]
                batch_best_answers_doc_ids = [x[0] for x in batch_best_answers_doc_ids]
                batch_best_answers_sentences = [x[0] for x in batch_best_answers_sentences]
            else:
                batch_best_answers = ["" for _ in questions_batch]
                batch_best_answers_place = [0 for _ in questions_batch]
                batch_best_answers_score = [0.0 for _ in questions_batch]
                batch_best_answers_doc_ids = ["" for _ in questions_batch]
                batch_best_answers_sentences = ["" for _ in questions_batch]

        if doc_ids_batch is None:
            if self.return_answer_sentence:
                return (
                    batch_best_answers,
                    batch_best_answers_score,
                    batch_best_answers_place,
                    batch_best_answers_sentences,
                )
            return batch_best_answers, batch_best_answers_score, batch_best_answers_place

        if self.return_answer_sentence:
            return (
                batch_best_answers,
                batch_best_answers_score,
                batch_best_answers_place,
                batch_best_answers_doc_ids,
                batch_best_answers_sentences,
            )
        return batch_best_answers, batch_best_answers_score, batch_best_answers_place, batch_best_answers_doc_ids
