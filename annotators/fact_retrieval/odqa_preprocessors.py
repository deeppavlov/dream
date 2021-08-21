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

import time
from logging import getLogger
from typing import Callable

from nltk import sent_tokenize

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

logger = getLogger(__name__)


@register("document_chunker")
class DocumentChunker(Component):
    """Make chunks from a document or a list of documents. Don't tear up sentences if needed.

    Args:
        sentencize_fn: a function for sentence segmentation
        keep_sentences: whether to tear up sentences between chunks or not
        tokens_limit: a number of tokens in a single chunk (usually this number corresponds to the squad model limit)
        flatten_result: whether to flatten the resulting list of lists of chunks
        paragraphs: whether to split document by paragrahs; if set to True, tokens_limit is ignored

    Attributes:
        keep_sentences: whether to tear up sentences between chunks or not
        tokens_limit: a number of tokens in a single chunk
        flatten_result: whether to flatten the resulting list of lists of chunks
        paragraphs: whether to split document by paragrahs; if set to True, tokens_limit is ignored

    """

    def __init__(
        self,
        sentencize_fn: Callable = sent_tokenize,
        keep_sentences: bool = True,
        tokens_limit: int = 400,
        flatten_result: bool = False,
        paragraphs: bool = False,
        number_of_paragraphs: int = -1,
        log: bool = False,
        *args,
        **kwargs,
    ) -> None:
        self._sentencize_fn = sentencize_fn
        self.keep_sentences = keep_sentences
        self.tokens_limit = tokens_limit
        self.flatten_result = flatten_result
        self.paragraphs = paragraphs
        self.number_of_paragraphs = number_of_paragraphs
        self.log = log

    def __call__(self, batch_docs):
        """Make chunks from a batch of documents. There can be several documents in each batch.
        Args:
            batch_docs: a batch of documents / a batch of lists of documents
        Returns:
            chunks of docs, flattened or not and
        """

        chunks_batch = []
        first_par_batch = []

        tm_st = time.time()
        for docs_list in batch_docs:
            first_par_list = []
            chunks_list = []
            for docs in docs_list:
                for doc in docs:
                    new_split_doc = []
                    if doc:
                        split_doc = doc.split("\n\n")
                        split_doc = [sd.strip() for sd in split_doc]
                        split_doc = list(filter(lambda x: len(x) > 40, split_doc))
                        if self.number_of_paragraphs != -1:
                            split_doc = split_doc[: self.number_of_paragraphs]
                        for par in split_doc:
                            sentences = sent_tokenize(par)
                            if len(sentences) <= 3:
                                new_split_doc.append(" ".join(sentences))
                            else:
                                num_pieces = len(sentences) // 2
                                for i in range(num_pieces):
                                    piece = " ".join(sentences[i * 2 : i * 2 + 3])
                                    piece_split = piece.split()
                                    new_split_doc.append(" ".join(piece_split[:150]))
                        if new_split_doc:
                            first_par_list.append(new_split_doc[0])

                    chunks_list += new_split_doc
            chunks_batch.append(chunks_list)
            first_par_batch.append(first_par_list)

        tm_end = time.time()
        if chunks_batch:
            logger.debug(f"chunking time {tm_end - tm_st}, number of chunks {len(chunks_batch[0])}")

        return chunks_batch, first_par_batch
