import json
from collections import Counter
import re

from nltk.tokenize import sent_tokenize


class Dial2seq:
    """
    a class to transform dialogues into a sequence of utterances and labels
    The sequence consists of n previous uterrances.

    There are no constraints
    on number of entities or midas types in the them, however a sequence is
    valid only when it is followed by an utterance with a single entity and
    its midas label is not MISC or ANAPHOR.

    params:
    path2data: str - a path to a json file with dialogues and their midas and cobot labels
    seqlen: int - a number of utterances to use to predict next midas labels and entities
    """

    def __init__(self, path2data: str, seqlen=2):
        self.data = self.__load_data(path2data)
        self.seqlen = seqlen

    def transform(self) -> list:
        """transforms dialogues into a set of sequences of size seqlen n+1"""
        return [seq for dial in self for seq in self.__ngrammer(dial)]

    def __ngrammer(self, dialogue: list) -> list:
        """transforms a dialogue into a set of sequences (ngram style)"""
        return [dialogue[i : i + self.seqlen + 1] for i in range(len(dialogue) - (self.seqlen + 1) + 1)]

    def __load_data(self, path: str) -> dict:
        """loads data from a json file"""
        with open(path, "r", encoding="utf8") as f:
            data = json.load(f)
        return data

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        """iterates over all the dialogues in the file"""
        for dialogue in self.data.values():
            yield dialogue


class SequencePreprocessor:
    """
    preprocesses sequences
    to filter only those that are relevant for the task

    params:
    num_entities: int - maximum size of a last sentence in a sequence
    in terms of number of annotated entities
    """

    def __init__(
        self,
        num_entities=1,
        stoplist_labels: list = ["misc", "anaphor"],
    ):
        self.num_entities = num_entities
        self.stoplist_labels = stoplist_labels
        self.midas_all = Counter()
        self.entity_all = Counter()
        self.midas_target = Counter()
        self.entity_target = Counter()
        self.midas_and_entity_target = Counter()

    def transform(self, sequences: list) -> list:
        """extract necessary data from sequences"""
        seqs = list()

        for seq in sequences:

            if not self.__is_valid(seq[-1]):
                continue

            sample = self.__get_dict_entry(self.__shape_output(seq))

            seqs.append(sample)

        return seqs

    def __is_valid(self, ut) -> bool:
        """
        checks if all the requirements for an utterance are met:
        1. an uterrance is one sentence, and has either one
        labelled entity which is not in the stoplist
        2. when an utterance has 2+ sentence, it will be valid if
        the requirement 2 is applicable to the first sentence while
        other sentences are omitted

        input:
        ut: dict

        output: bool
        """
        # skip those that have too many entities
        if len(ut["entities"][0]) > 1:
            return False

        # no entities in the first or only sentence
        if not ut["entities"][0]:
            return True

        # if there is one, check if it is not in stoplist of entity labels
        return ut["entities"][0][0]["label"] not in self.stoplist_labels

    def __shape_output(self, seq: list) -> list:
        """shapes sequence in order to keep only the necessary data"""

        output = list()

        for ut in seq[:-1]:
            midas_labels, midas_vectors = self.__get_midas(ut["midas"])

            output.append((ut["text"], midas_labels, midas_vectors, ut["entities"]))

        # preprocess last sentence in the sequence
        midas_labels, midas_vectors = self.__get_midas(seq[-1]["midas"])
        sentence = seq[-1]["text"][0]
        entity = seq[-1]["entities"][0]
        # if there is an entity, take it. Otherwise, use dict of empty values
        entity = entity[0] if entity else {"label": "", "offsets": [0, 0], "text": ""}

        # replace the entity text with its label
        sentence = sentence[: entity["offsets"][0]] + entity["label"].upper() + sentence[entity["offsets"][1] :]

        output.append((sentence, midas_labels[0:1], entity))

        return output

    def __get_dict_entry(self, seq) -> dict:
        """creates a proper dict entry to dump into a file"""
        entry = dict()

        # calc stats for all possible entities and targets in prev sequences
        for s in seq[:-1]:
            self.midas_all.update(s[1])
            self.entity_all.update([ent["label"] for ents in s[-1] for ent in ents])

        # calc stats for targets
        self.midas_target.update([seq[-1][1][0]])
        self.entity_target.update([seq[-1][2]["label"]])
        self.midas_and_entity_target.update([f"{seq[-1][1][0]}_{seq[-1][2]['label']}"])

        entry["previous_text"] = [s[0] for s in seq[:-1]]
        entry["previous_midas"] = [s[1] for s in seq[:-1]]
        entry["midas_vectors"] = [s[2] for s in seq[:-1]]
        entry["previous_entities"] = [s[-1] for s in seq[:-1]]
        entry["predict"] = {}
        entry["predict"]["text"] = seq[-1][0]
        entry["predict"]["midas"] = seq[-1][1][0]
        entry["predict"]["entity"] = seq[-1][2]

        return entry

    def __get_midas(self, midas_labels: list) -> tuple:
        """
        extracts midas labels with max value per each sentence in an utterance
        and return a midas vector per each sentence
        """
        labels = []
        vectors = []

        for sample in midas_labels:
            labels.append(max(sample[0], key=sample[0].get))
            vectors.append(list(sample[0].values()))

        return labels, vectors
