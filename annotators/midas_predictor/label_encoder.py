import re

from abc import ABC, abstractmethod
from hashlib import sha1
from typing import List, Tuple

from sklearn.preprocessing import MultiLabelBinarizer
from tqdm import tqdm

import spacy

spacy.prefer_gpu()
nlp = spacy.load("en_core_web_sm")

Labels = List[Tuple[str, str]]
EncodedLabels = List[List[int]]


class LabelEncoder:
    """
    Returns encoded labels in the following formats:
    1. Midas labels only
    2. Entity labels only
    3. Their concatenation
    4. Multilabeled binarization.

    First three
    The first two will be used when a separate classifier is applied
    while their concatenation is used with a universal classifier.
    Multilabeled binarization is based on sklearn MultiLabelBinarizer
    """

    def __init__(self, classes: list, encoding: str = 'multi'):
        self.mlb = MultiLabelBinarizer()
        self.mlb.classes = classes
        self.encoding = self.__validate_encoding(encoding)

    def to_categorical(self, labels: Labels) -> EncodedLabels:
        """ encodes labels for tensorflow models """
        if self.encoding == 'midas':
            labels = [sample[:1] for sample in labels]
        elif self.encoding == 'entity':
            labels = [sample[1:] for sample in labels]
        elif self.encoding == 'concatenation':
            labels = [["_".join(sample)] for sample in labels]

        return self.mlb.fit_transform(labels)

    def __validate_encoding(self, encoding: str) -> str:
        # validates encoding type
        err_message = "Sorry, choose one of those: 'midas', 'entity', 'concatenation', 'multi'"
        assert encoding in ['midas', 'entity', 'concatenation', 'multi'], err_message
        return encoding


def dummy_fn(doc):
    """ dummy function to apply tfidf to pre-tokenized docs """
    return doc


def spacy_tokenize(text: str, tokenizer):
    """
    tokenize a string with Spacy and return list of lowercase tokens
    """
    return [token.lower_ for token in tokenizer(text)]


class Raw2Clean(ABC):
    """
    a class to transform raw dialogues into clean ones with a legacy structure
    """

    def __init__(self, data, output_path: str):
        self.data = data
        self.output_path = output_path

    @abstractmethod
    def clean(self):
        """ reduces a dataset to necessary data only"""
        pass


class Daily2Clean(Raw2Clean):
    """ Raw2Clean customisation for the daily dialogue dataset """

    def clean(self):
        output = {}

        for dialogue in tqdm(self.data):
            idx = sha1(dialogue.encode()).hexdigest()
            output[idx] = [{'text': self.__preproc(ut)} for ut in dialogue.split('__eou__') if ut.strip()]

        return output

    def __preproc(self, text: str) -> list:
        """
        removes unnecessary spaces from a string and
        tokenizes into sentences to facilitate midas annotation
        """
        # remove extra spaces between punctuation marks and word tokens
        text = re.sub(r'(?<=[a-zA-Z0-9\.,?!])\s(?=[\.,?!])', "", text.strip())
        # remove extra spaces in acronyms to faciliate midas annotation
        text = re.sub(r'(?<=[A-Z]\.)\s(?=[A-Z])', "", text)
        # tokenize into sentences
        return [s.text for s in nlp(text).sents]


class Topical2Clean(Raw2Clean):
    """ Raw2Clean customisation for the topical chat dataset """

    def clean(self):
        output = {}

        for idx, sample in tqdm(self.data.items()):
            output[idx] = [{'text': self.__preproc(ut['message'])} for ut in sample['content']]

        return output

    def __preproc(self, text: str) -> list:
        """
        replaces all commas with full stops and tokenize into sentences
        """
        return [s.text for s in nlp(text.replace(",", ".")).sents if s.text.strip()]
