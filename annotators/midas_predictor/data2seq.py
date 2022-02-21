import json


class Dial2seq:
    """
    a class to transform dialogues into a sequence of utterances and labels
    The sequence consists of n previous uterrances.

    params:
    path2data: str - a path to a json file with dialogues and their midas annotation
    seqlen: int - a number of utterances to use to predict next midas labels,
    i.e. context length
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
    Prepares a dataset for training - can be updated with filters,
    e.g., to filter out invalid sequences
    """

    def transform(self, sequences: list) -> list:
        """extract necessary data from sequences"""
        seqs = list()

        for seq in sequences:
            sample = self.__get_dict_entry(self.__shape_output(seq))
            seqs.append(sample)

        return seqs

    def __shape_output(self, seq: list) -> list:
        """shapes sequence in order to keep only the necessary data"""

        output = list()

        for ut in seq[:-1]:

            midas_labels, midas_vectors = self.__get_midas(ut["midas"])

            output.append((ut["text"], midas_labels, midas_vectors))

        # preprocess only the first sentence of
        # the last utterance in the sequence
        midas_labels, midas_vectors = self.__get_midas(seq[-1]["midas"])
        midas_labels, midas_vectors = midas_labels[0:1], midas_vectors[0:1]
        sentence = seq[-1]["text"][0]

        output.append((sentence, midas_labels[0:1]))

        return output

    def __get_dict_entry(self, seq) -> dict:
        """creates a proper dict entry to dump into a file"""
        entry = dict()
        entry["previous_text"] = [s[0] for s in seq[:-1]]
        entry["previous_midas"] = [s[1] for s in seq[:-1]]
        entry["midas_vectors"] = [s[2] for s in seq[:-1]]
        entry["predict"] = {}
        entry["predict"]["text"] = seq[-1][0]
        entry["predict"]["midas"] = seq[-1][1][0]

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
