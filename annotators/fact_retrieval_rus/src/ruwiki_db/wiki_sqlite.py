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

import sqlite3
from logging import getLogger

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.commands.utils import expand_path

logger = getLogger(__name__)


@register("wiki_sqlite_vocab")
class WikiSQLiteVocab(Component):
    def __init__(self, load_path: str, shuffle: bool = False, top_n: int = 2, **kwargs) -> None:
        load_path = str(expand_path(load_path))
        self.top_n = top_n
        logger.info("Connecting to database, path: {}".format(load_path))
        try:
            self.connect = sqlite3.connect(load_path, check_same_thread=False)
        except sqlite3.OperationalError as e:
            e.args = e.args + ("Check that DB path exists and is a valid DB file",)
            raise e
        try:
            self.db_name = self.get_db_name()
        except TypeError as e:
            e.args = e.args + (
                "Check that DB path was created correctly and is not empty. "
                "Check that a correct dataset_format is passed to the ODQAReader config",
            )
            raise e
        self.doc_ids = self.get_doc_ids()
        self.doc2index = self.map_doc2idx()

    def __call__(self, par_ids_batch, entities_pages_batch, *args, **kwargs):
        all_contents, all_contents_ids, all_pages, all_from_linked_page, all_numbers = [], [], [], [], []
        for entities_pages, par_ids in zip(entities_pages_batch, par_ids_batch):
            page_contents, page_contents_ids, pages, from_linked_page, numbers = [], [], [], [], []
            for entity_pages in entities_pages:
                for entity_page in entity_pages[: self.top_n]:
                    cur_page_contents, cur_page_contents_ids, cur_pages = self.get_page_content(entity_page)
                    page_contents += cur_page_contents
                    page_contents_ids += cur_page_contents_ids
                    pages += cur_pages
                    from_linked_page += [True for _ in cur_pages]
                    numbers += list(range(len(cur_pages)))

            par_contents = []
            par_pages = []
            for par_id in par_ids:
                text, page = self.get_paragraph_content(par_id)
                par_contents.append(text)
                par_pages.append(page)
                from_linked_page.append(False)
                numbers.append(0)
            all_contents.append(page_contents + par_contents)
            all_contents_ids.append(page_contents_ids + par_ids)
            all_pages.append(pages + par_pages)
            all_from_linked_page.append(from_linked_page)
            all_numbers.append(numbers)

        return all_contents, all_contents_ids, all_pages, all_from_linked_page, all_numbers

    def get_paragraph_content(self, par_id):
        cursor = self.connect.cursor()
        cursor.execute("SELECT text, doc FROM {} WHERE title = ?".format(self.db_name), (par_id,))
        result = cursor.fetchone()
        cursor.close()
        return result

    def get_page_content(self, page):
        page = page.replace("_", " ")
        cursor = self.connect.cursor()
        cursor.execute("SELECT text, title FROM {} WHERE doc = ?".format(self.db_name), (page,))
        result = cursor.fetchall()
        paragraphs = [elem[0] for elem in result]
        titles = [elem[1] for elem in result]
        pages = [page for _ in result]
        cursor.close()
        return paragraphs, titles, pages

    def get_doc_ids(self):
        cursor = self.connect.cursor()
        cursor.execute("SELECT title FROM {}".format(self.db_name))
        ids = [ids[0] for ids in cursor.fetchall()]
        cursor.close()
        return ids

    def get_db_name(self):
        cursor = self.connect.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        assert cursor.arraysize == 1
        name = cursor.fetchone()[0]
        cursor.close()
        return name

    def map_doc2idx(self):
        doc2idx = {doc_id: i for i, doc_id in enumerate(self.doc_ids)}
        logger.info("SQLite iterator: The size of the database is {} documents".format(len(doc2idx)))
        return doc2idx
