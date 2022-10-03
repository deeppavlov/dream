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
import pymorphy2
from rusenttokenize import ru_sent_tokenize
from deeppavlov.core.common.registry import register

logger = getLogger(__name__)


@register("filter_docs")
class FilterDocs:
    def __init__(self, top_n, log_filename: str = None, filter_flag=True, **kwargs):
        self.top_n = top_n
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        self.lemmatizer = pymorphy2.MorphAnalyzer()
        self.filter_flag = filter_flag
        self.log_filename = log_filename
        self.cnt = 0

    def __call__(self, questions, batch_doc_ids, batch_doc_text, batch_doc_pages):
        self.cnt += 1
        tm_st = time.time()
        batch_filtered_doc_ids = []
        batch_filtered_docs = []
        batch_filtered_doc_pages = []
        for question, doc_ids, doc_text, doc_pages in zip(questions, batch_doc_ids, batch_doc_text, batch_doc_pages):
            if self.filter_flag:
                if self.log_filename:
                    out = open(f"{self.log_filename}", "a")
                    out.write("before ranking" + "\n")
                    out.write("=" * 50 + "\n")
                    for n, (doc_id, doc, doc_page) in enumerate(zip(doc_ids, doc_text, doc_pages)):
                        out.write(f"---- {n} {doc_id} {doc_page}" + "\n")
                        out.write(str(doc) + "\n")
                        out.write("_" * 50 + "\n")
                    out.write("^" * 50 + "\n")
                    out.close()
                docs_and_ids = list(zip(doc_ids, doc_text, doc_pages))
                docs_and_ids = [elem for elem in docs_and_ids if elem[1] is not None]
                doc_ids, doc_text, doc_pages = zip(*docs_and_ids)
                doc_ids = list(doc_ids)
                doc_text = list(doc_text)
                doc_pages = list(doc_pages)
                filtered_doc_ids, filtered_docs, filtered_doc_pages = self.filter_what_is(
                    question, doc_ids, doc_text, doc_pages
                )
                filtered_doc_ids, filtered_docs, filtered_doc_pages = self.filter_docs(
                    question, filtered_doc_ids, filtered_docs, filtered_doc_pages
                )
                filtered_doc_ids, filtered_docs, filtered_doc_pages = self.split_paragraphs(
                    question, filtered_doc_ids, filtered_docs, filtered_doc_pages
                )
                if self.log_filename:
                    out = open(f"{self.log_filename}", "a")
                    out.write("after ranking" + "\n")
                    for n, (doc_id, doc, doc_page) in enumerate(
                        zip(filtered_doc_ids, filtered_docs, filtered_doc_pages)
                    ):
                        out.write(f"---- {n} {doc_id} {doc_page}" + "\n")
                        out.write(str(doc) + "\n")
                        out.write("_" * 50 + "\n")
                    out.close()
            else:
                filtered_doc_ids = doc_ids
                filtered_docs = doc_text
                filtered_doc_pages = doc_pages

            batch_filtered_doc_ids.append(filtered_doc_ids[: self.top_n])
            # batch_filtered_docs.append(self.replace_brackets(filtered_docs[:self.top_n]))
            batch_filtered_docs.append(filtered_docs[: self.top_n])
            batch_filtered_doc_pages.append(filtered_doc_pages[: self.top_n])
        tm_end = time.time()
        print("filter docs", tm_end - tm_st)

        return batch_filtered_doc_ids, batch_filtered_docs, batch_filtered_doc_pages

    def filter_what_is(self, question, doc_ids, docs, doc_pages):
        """If the question is "What is ...?", for example, "What is photon?", the function extracts the entity
        (for example, "photon") and sorts the paragraphs so that the paragraphs with the title ("doc_id")
        which contain the entity, get higher score
        """
        if "что такое" in question.lower():
            docs_with_scores = []
            what_is_ent = re.findall(r"что такое (.*?)\?", question.lower())
            for n, (doc, doc_id, doc_page) in enumerate(zip(docs, doc_ids, doc_pages)):
                if what_is_ent[0] == doc_id.lower():
                    docs_with_scores.append((doc_id, doc, doc_page, 10, len(docs) - n))
                elif what_is_ent[0] == doc_id.split(", ")[0].lower():
                    docs_with_scores.append((doc_id, doc, doc_page, 5, len(docs) - n))
                else:
                    docs_with_scores.append((doc_id, doc, doc_page, 0, len(docs) - n))
            docs_with_scores = sorted(docs_with_scores, key=lambda x: (x[3], x[4]), reverse=True)
            docs = [elem[1] for elem in docs_with_scores]
            doc_ids = [elem[0] for elem in docs_with_scores]
            doc_pages = [elem[2] for elem in docs_with_scores]
        return doc_ids, docs, doc_pages

    def replace_brackets(self, docs_list):
        """Function which deletes redundant symbols from paragraphs"""
        new_docs_list = []
        for doc in docs_list:
            fnd = re.findall(r"(\(.*[\d]{3,4}.*\))", doc)
            if fnd:
                new_docs_list.append(doc.replace(fnd[0], "").replace("  ", " "))
            else:
                new_docs_list.append(doc)
        return new_docs_list

    def split_paragraphs(self, question, doc_ids, docs, doc_pages):
        """If the question is "What is the ...est ... in ...?", the function processed paragraphs with candidate
        answers to leave in each paragraph only the sentence about "the ...est ...".
        Such preprocessing of paragraphs make it easier for SQuAD model to find answer.
        """
        filtered_doc_ids, filtered_docs, filtered_doc_pages = [], [], []
        if any([word in question.lower() for word in {"самый", "самая", "самое", "самым", "самой", "самые"}]):
            for doc, doc_id, doc_page in zip(docs, doc_ids, doc_pages):
                sentences = ru_sent_tokenize(doc)
                for sentence in sentences:
                    if any(
                        [word in sentence.lower() for word in {"самый", "самая", "самое", "самым", "самой", "самые"}]
                    ):
                        filtered_doc_ids.append(doc_id)
                        filtered_docs.append(sentence)
                        filtered_doc_pages.append(doc_page)
                    else:
                        sentence_tokens = re.findall(self.re_tokenizer, sentence)
                        if (
                            any([tok.endswith("ейший") for tok in sentence_tokens])
                            or any([tok.endswith("ейшая") for tok in sentence_tokens])
                            or any([tok.endswith("ейшее") for tok in sentence_tokens])
                        ):
                            filtered_doc_ids.append(doc_id)
                            filtered_docs.append(sentence)
                            filtered_doc_pages.append(doc_page)
        else:
            filtered_doc_ids = doc_ids
            filtered_docs = docs
            filtered_doc_pages = doc_pages

        return filtered_doc_ids, filtered_docs, filtered_doc_pages

    def filter_docs(self, question, doc_ids, docs, doc_pages):
        """If the question contains the year, the function leaves the paragraphs which contain the year.
        If the question is about distance from one place to another, the function checks if the
        paragraph contain these entities.
        """
        new_doc_ids, new_docs, new_doc_pages = [], [], []
        used_docs_and_ids = set()
        for doc_id, doc, doc_page in zip(doc_ids, docs, doc_pages):
            if (doc_id, doc, doc_page) not in used_docs_and_ids:
                new_doc_ids.append(doc_id)
                new_docs.append(doc)
                new_doc_pages.append(doc_page)
                used_docs_and_ids.add((doc_id, doc, doc_page))
        doc_ids = new_doc_ids
        docs = new_docs
        doc_pages = new_doc_pages

        dist_pattern = re.findall(r"расстояние от ([\w]+) до ([\w]+)", question)
        found_year = re.findall(r"[\d]{4}", question)
        filtered_docs = []
        filtered_doc_ids = []
        filtered_doc_pages = []
        if dist_pattern:
            places = list(dist_pattern[0])
            lemm_places = []
            lemm_doc_ids = []
            lemm_docs = []
            for place in places:
                place_tokens = re.findall(self.re_tokenizer, place)
                place_tokens = [tok for tok in place_tokens if len(tok) > 2]
                lemm_place = [self.lemmatizer.parse(tok)[0].normal_form for tok in place_tokens]
                lemm_places.append(" ".join(lemm_place))
            for doc in docs:
                doc_tokens = re.findall(self.re_tokenizer, doc)
                doc_tokens = [tok for tok in doc_tokens if len(tok) > 2]
                lemm_doc = [self.lemmatizer.parse(tok)[0].normal_form for tok in doc_tokens]
                lemm_docs.append(" ".join(lemm_doc))
            for doc_id in doc_ids:
                doc_tokens = re.findall(self.re_tokenizer, doc_id)
                doc_tokens = [tok for tok in doc_tokens if len(tok) > 2]
                lemm_doc = [self.lemmatizer.parse(tok)[0].normal_form for tok in doc_tokens]
                lemm_doc_ids.append(" ".join(lemm_doc))

            for doc_id, doc, doc_page, lemm_doc_id, lemm_doc in zip(doc_ids, docs, doc_pages, lemm_doc_ids, lemm_docs):
                count = 0
                for place in lemm_places:
                    if place in lemm_doc or place in lemm_doc_id:
                        count += 1
                if count >= len(lemm_places):
                    filtered_docs.append(doc)
                    filtered_doc_ids.append(doc_id)
                    filtered_doc_pages.append(doc_page)
        elif found_year:
            for doc, doc_id, doc_page in zip(docs, doc_ids, doc_pages):
                if found_year[0] in doc:
                    filtered_docs.append(doc)
                    filtered_doc_ids.append(doc_id)
                    filtered_doc_pages.append(doc_page)
        else:
            filtered_docs = docs
            filtered_doc_ids = doc_ids
            filtered_doc_pages = doc_pages

        return filtered_doc_ids, filtered_docs, filtered_doc_pages
