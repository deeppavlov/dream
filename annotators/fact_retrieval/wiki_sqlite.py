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

import os
import time
import logging

import sentry_sdk

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.dataset_iterators.sqlite_iterator import SQLiteDataIterator

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


@register("wiki_sqlite_vocab")
class WikiSQLiteVocab(SQLiteDataIterator, Component):
    """Get content from SQLite database by document ids.

    Args:
        load_path: a path to local DB file
        join_docs: whether to join extracted docs with ' ' or not
        shuffle: whether to shuffle data or not

    Attributes:
        join_docs: whether to join extracted docs with ' ' or not

    """

    def __init__(self, load_path, join_docs=True, shuffle=False, **kwargs):
        SQLiteDataIterator.__init__(self, load_path=load_path, shuffle=shuffle)
        self.join_docs = join_docs

    def __call__(self, doc_ids_batch=None, *args, **kwargs):
        """Get the contents of files, stacked by space or as they are.

        Args:
            doc_ids: a batch of lists of ids to get contents for

        Returns:
            a list of contents / list of lists of contents
        """
        tm_st = time.time()
        contents_batch = []
        logger.info(f"doc_ids_batch {doc_ids_batch}")
        for ids_list in doc_ids_batch:
            contents_list = []
            for ids in ids_list:
                contents = [self.get_doc_content(doc_id) for doc_id in ids]
                logger.debug(f"contents {contents}")
                if self.join_docs:
                    contents = " ".join(contents)
                contents_list.append(contents)
            contents_batch.append(contents_list)
        tm_end = time.time()
        logger.debug(f"sqlite vocab time {tm_end - tm_st}")

        return contents_batch
