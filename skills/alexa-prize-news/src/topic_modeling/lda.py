import re
from collections import defaultdict
from functools import partial
from typing import Tuple, List, Dict, Callable

import gensim
from gensim.models import LdaModel, TfidfModel
from gensim.utils import simple_tokenize
from nltk import sent_tokenize
from tqdm import tqdm

from src.consts import (
    SubtopicSummaryType,
    LDA_MODEL_PATH,
    LDA_DICT_PATH,
    LDA_PARAMETERS_PATH,
    LDA_SUBTOPICS_PATH,
    LDA_SUBTOPIC_KEY_WORDS_PATH,
    LDA_SUBTOPIC_KEY_PHRASES_PATH,
    LDA_SUBTOPIC_N_WORDS_PATH,
    LDA_SUBTOPIC_SENTENCE_PATH,
    MAX_SUBTOPICS_NUM,
    SUBTOPIC_SUMMARY_TYPE,
    N_BASE_UNIGRAMS,
    N_PARAMETER
)
from src.topic_modeling.utils import (
    check_parameters,
    load_subtopic_summaries,
    remove_subtopic_summaries,
    get_parameters,
    original_topic2topic,
    paired,
    preprocess
)
from src.utils import load, save


class LDA(object):
    def __init__(self, log):
        self.model = None
        self.dictionary = None
        self.subtopics_news_indices = None
        self.subtopic_summaries = None
        self.subtopic_parameters = None
        self._log = log

    def load(self):
        fields = {
            "model": load(LDA_MODEL_PATH),
            "dictionary": load(LDA_DICT_PATH),
            "subtopics_news_indices": load(LDA_SUBTOPICS_PATH),
            "subtopic_summaries": load_subtopic_summaries(),
            "subtopic_parameters": check_parameters(load(LDA_PARAMETERS_PATH))
        }
        if None not in fields.values():
            self.model = fields["model"]
            self.dictionary = fields["dictionary"]
            self.subtopics_news_indices = fields["subtopics_news_indices"]
            self.subtopic_summaries = fields["subtopic_summaries"]
            self.subtopic_parameters = fields["subtopic_parameters"]
        else:
            self._log("Could not load LDA models.")
        return self

    def update(self, texts):
        self._log("Starting LDA models training.")

        index, sections = self.__get_sections(texts)
        sentences, processed_sentences = self.__preprocess_sentences(index, sections)
        processed_docs = self.__preprocess_docs(processed_sentences)
        dictionary = self.__create_dictionary(sections, processed_docs)
        bow_corpus = self.__create_bow_corpus(processed_docs, dictionary)
        tf_idf_corpus = self.__create_tf_idf_corpus(bow_corpus)

        self.model = self.__create_lda_model(dictionary, bow_corpus, tf_idf_corpus)
        self.dictionary = dictionary
        self.subtopics_news_indices = self.__assign_subtopics(self.model, bow_corpus, index)
        self.subtopic_summaries = self.__subtopics_summaries(sentences, processed_sentences)
        self.subtopic_parameters = get_parameters()

        self._log("Finishing LDA models training.")
        return self

    def save(self):
        fields = [
            self.model,
            self.dictionary,
            self.subtopics_news_indices,
            self.subtopic_summaries,
            self.subtopic_parameters
        ]
        if None not in fields:
            save(LDA_MODEL_PATH, self.model)
            save(LDA_DICT_PATH, self.dictionary)
            save(LDA_SUBTOPICS_PATH, self.subtopics_news_indices)
            save(LDA_PARAMETERS_PATH, self.subtopic_parameters)

            remove_subtopic_summaries()
            if SUBTOPIC_SUMMARY_TYPE == SubtopicSummaryType.KEY_PHRASES:
                save(LDA_SUBTOPIC_KEY_PHRASES_PATH, self.subtopic_summaries[SubtopicSummaryType.KEY_PHRASES])
            else:
                save(LDA_SUBTOPIC_KEY_WORDS_PATH, self.subtopic_summaries[SubtopicSummaryType.KEY_WORDS])
                save(LDA_SUBTOPIC_N_WORDS_PATH, self.subtopic_summaries[SubtopicSummaryType.N_WORDS])
                save(LDA_SUBTOPIC_SENTENCE_PATH, self.subtopic_summaries[SubtopicSummaryType.SENTENCE])
        else:
            self._log("Could not save LDA models.")
        return self

    def get_subtopics_summaries(self, topic: str) -> List[Tuple[int, str]]:
        if topic not in self.model:
            return []
        return self.subtopic_summaries[topic]

    def get_topics(self) -> List[str]:
        topics = self.subtopics_news_indices.keys()
        topics = [t for t in topics if t]
        return topics

    def __get_sections(self, texts):
        not_found = defaultdict(int)

        index = defaultdict(list)
        sections = defaultdict(list)
        for i, text in enumerate(texts):
            if 'primarysection' in text:
                topic = text['primarysection']
                if topic in original_topic2topic:
                    topic = original_topic2topic[topic]
                else:
                    not_found[topic] += 1
                    topic = "other"
                topic = topic.lower()
                topic = re.sub(r"[^a-z ]+", " ", topic)
                topic = re.sub(r" +", " ", topic)
                topic = topic.strip()

                if topic:
                    index[topic].append(i)
                    sections[topic].append(text['body'])
        not_found = sorted(not_found.items(), key=lambda x: x[1], reverse=True)
        for k, v in not_found:
            self._log(f"Topic `{k}` was not found {v} times. Replaced with `other`.")
        return index, sections

    @staticmethod
    def __preprocess_sentences(
            index: Dict[str, List[int]],
            sections: Dict[str, List[str]]
    ) -> Tuple[Dict[str, Dict[int, List[List[str]]]], Dict[str, Dict[int, List[List[str]]]]]:
        sentences = {topic: defaultdict(list) for topic in sections}
        processed_sentences = {topic: defaultdict(list) for topic in sections}

        for topic in tqdm(sections, desc="Preprocess"):
            for i, doc in zip(index[topic], sections[topic]):
                for sentence in sent_tokenize(doc):
                    sentence = [w for w in simple_tokenize(sentence)]
                    stemmed = [preprocess(w) for w in sentence]

                    sentences[topic][i].append(sentence)
                    processed_sentences[topic][i].append(stemmed)

        return sentences, processed_sentences

    @staticmethod
    def __preprocess_docs(
            processed_sentences: Dict[str, Dict[int, List[List[str]]]]
    ) -> Dict[str, List[List[str]]]:
        processed_docs = defaultdict(list)
        for topic in processed_sentences:
            for doc in processed_sentences[topic].values():
                words = [w for sentence in doc for w in sentence if w]
                if SUBTOPIC_SUMMARY_TYPE == SubtopicSummaryType.KEY_PHRASES:
                    words = paired(words)
                processed_docs[topic].append(words)
        return processed_docs

    @staticmethod
    def __create_dictionary(sections: dict, processed_docs: dict):
        dictionary = {}
        for topic in sections:
            dictionary[topic] = gensim.corpora.Dictionary(processed_docs[topic])
        return dictionary

    @staticmethod
    def __create_bow_corpus(processed_docs: dict, dictionary: dict):
        bow_corpus = {}
        for topic in processed_docs:
            bow_corpus[topic] = [dictionary[topic].doc2bow(doc) for doc in processed_docs[topic]]

        return bow_corpus

    @staticmethod
    def __create_tf_idf_corpus(bow_corpus: dict):
        corpus_tfidf = {}
        for topic in bow_corpus:
            tfidf = TfidfModel(bow_corpus[topic])
            corpus_tfidf[topic] = tfidf[bow_corpus[topic]]

        return corpus_tfidf

    @staticmethod
    def __create_lda_model(dictionary, bow_corpus, corpus):
        model = {}
        for topic in tqdm(bow_corpus, desc="LDA models"):
            num_topics = len(bow_corpus[topic]) // 10
            num_topics = min(num_topics, MAX_SUBTOPICS_NUM)
            if num_topics < 2:
                continue

            model[topic] = LdaModel(
                corpus=corpus[topic],
                id2word=dictionary[topic],
                num_topics=num_topics,
                iterations=100,
                passes=3
            )
        return model

    @staticmethod
    def __assign_subtopics(model, bow_corpus: dict, index: dict):
        subtopics = {}
        for topic in bow_corpus:
            subtopics[topic] = defaultdict(set)
            for i, doc in zip(index[topic], bow_corpus[topic]):
                if topic in model:
                    distribution = model[topic].get_document_topics(doc)
                    subtopic = max(distribution, key=lambda x: x[1])[0]
                    subtopics[topic][subtopic].add(i)
                else:
                    subtopics[topic][0].add(i)
        return subtopics

    @staticmethod
    def __get_original_subtopic_phrases(sentences: List[List[str]],
                                        stemmed_sentences: List[List[str]],
                                        stemmed_grams: List[str]) -> str:
        stemmed_grams = stemmed_grams[:N_PARAMETER]
        result = ['' for _ in stemmed_grams]

        words, stemmed = [], []
        for sentence, stemmed_sentence in zip(sentences, stemmed_sentences):
            words.extend(sentence)
            stemmed.extend(stemmed_sentence)

        last_j = None
        for j, w in enumerate(reversed(stemmed)):
            if not w:
                continue

            if last_j is not None:
                pair = w[0] + " " + stemmed[last_j][0]

                for k, p in enumerate(stemmed_grams):
                    if p == pair:
                        phrase = words[-(j + 1):last_j + 1]
                        phrase = ' '.join(phrase)
                        if not result[k] or len(result[k]) > len(phrase):
                            result[k] = phrase
            last_j = len(stemmed) - (j + 1)

        result = [r if r else p for r, p in zip(result, stemmed_grams)]
        result = ', '.join(result)
        return result

    @staticmethod
    def __get_subtopic_n_words_summary(sentences: List[List[str]],
                                       stemmed_sentences: List[List[str]],
                                       stemmed_grams: List[str]) -> str:
        max_count = 0
        result = ""
        for sentence, stemmed_sentence in zip(sentences, stemmed_sentences):
            if len(sentence) > N_PARAMETER:
                for i in range(len(sentence) - N_PARAMETER + 1):
                    text = ' '.join(sentence[i:i + N_PARAMETER])
                    stemmed = stemmed_sentence[i:i + N_PARAMETER]
                    current = sum([w in stemmed_grams for w in stemmed])
                    if current > max_count:
                        max_count = current
                        result = text
            else:
                current = sum([w in stemmed_grams for w in stemmed_sentence])
                if current > max_count:
                    max_count = current
                    result = ' '.join(sentence)
        return result

    @staticmethod
    def __get_subtopic_sentence_summary(sentences: List[List[str]],
                                        stemmed_sentences: List[List[str]],
                                        stemmed_grams: List[str]) -> str:
        max_count = 0
        result = ""
        for sentence, stemmed in zip(sentences, stemmed_sentences):
            current = sum([w in stemmed_grams for w in stemmed])
            if current > max_count:
                max_count = current
                result = ' '.join(sentence)
        return result

    def __subtopics_summaries_with(self,
                                   sentences: Dict[str, Dict[int, List[List[str]]]],
                                   processed_sentences: Dict[str, Dict[int, List[List[str]]]],
                                   get_summary: Callable[[List[List[str]], List[List[str]], List[str]], str],
                                   desc: str
                                   ) -> Dict[str, List[Tuple[int, str]]]:
        result = {}
        for topic in tqdm(self.model, desc=f"Compute {desc} summaries"):
            result[topic] = []
            subtopics_stemmed = self.model[topic].show_topics(-1, num_words=N_BASE_UNIGRAMS, formatted=False)

            for i, stemmed_grams in subtopics_stemmed:
                stemmed_grams = [x for x, _ in stemmed_grams]
                doc_ids = self.subtopics_news_indices[topic][i]
                if doc_ids:
                    subtopic_sentences = []
                    subtopic_stemmed_sentences = []
                    for (j, doc), (_, stemmed_doc) in zip(sentences[topic].items(), processed_sentences[topic].items()):
                        if j in doc_ids:
                            for sentence, stemmed in zip(doc, stemmed_doc):
                                subtopic_sentences.append(sentence)
                                subtopic_stemmed_sentences.append(stemmed)
                    summary = get_summary(subtopic_sentences, subtopic_stemmed_sentences, stemmed_grams)
                    result[topic].append((i, summary))
        return result

    def __subtopics_summaries(
            self,
            sentences: Dict[str, Dict[int, List[List[str]]]],
            processed_sentences: Dict[str, Dict[int, List[List[str]]]]
    ) -> Dict[SubtopicSummaryType, Dict[str, List[Tuple[int, str]]]]:
        subtopic_summary_with = partial(self.__subtopics_summaries_with, sentences, processed_sentences)

        key_phrases = subtopic_summary_with(LDA.__get_original_subtopic_phrases, "Key Phrases")
        key_words = subtopic_summary_with(lambda _1, _2, stemmed_grams:
                                          ', '.join(stemmed_grams[:N_PARAMETER]), "Key Words")
        n_words = subtopic_summary_with(LDA.__get_subtopic_n_words_summary, "N Words")
        sentence = subtopic_summary_with(LDA.__get_subtopic_sentence_summary, "Sentence")

        type2summaries = {
            SubtopicSummaryType.KEY_PHRASES: key_phrases,
            SubtopicSummaryType.KEY_WORDS: key_words,
            SubtopicSummaryType.N_WORDS: n_words,
            SubtopicSummaryType.SENTENCE: sentence
        }
        return type2summaries
