import numpy as np
from tensorflow.keras.utils import Sequence


class MidasDataset(Sequence):
    """customized Dataset class from tensorflow"""

    def __init__(self, data: list, vectorizer, batch_size: int = 32, shuffle: bool = False):
        self.data = data
        self.indexes = np.arange(len(self.data))
        self.vectorizer = vectorizer
        self.batch_size = batch_size
        self.shuffle = shuffle

    def __len__(self):
        """
        Denotes the number of batches per epoch
        A common practice is to set this value to [num_samples / batch size⌋
        so that the model sees the training samples at most once per epoch.
        """
        return int(np.ceil(len(self.data) / self.batch_size))

    def on_epoch_end(self):
        """
        Updates indexes after each epoch
        Shuffling the order so that batches between epochs do not look alike.
        It can make a model more robust.
        """
        if self.shuffle:
            np.random.shuffle(self.indexes)

    def __getitem__(self, idx: int):
        """get batch_id and return its vectorized representation"""
        indexes = self.indexes[idx * self.batch_size : (idx + 1) * self.batch_size]
        batch = [self.data[index] for index in indexes]

        x_batch = np.zeros([len(batch), self.vectorizer.vector_size])
        y_batch = list()

        for i, sample in enumerate(batch):
            x_batch[i, :] = self.vectorizer.context_vector(sample["previous_text"], sample["midas_vectors"])
            y_batch.append(sample["predict"]["midas"])

        # encode labels
        y_batch = [self.vectorizer.midas2id[label] for label in y_batch]

        return x_batch, y_batch


class MidasVectorizer:
    def __init__(self, text_vectorizer, midas2id: dict, context_len: int = 3, embed_dim: int = 512):
        self.vectorizer = text_vectorizer  # USE
        self.midas2id = midas2id
        self.context_len = context_len
        self.utterance_vec_size = embed_dim + len(midas2id)
        self.vector_size = self.context_len * self.utterance_vec_size

    def context_vector(self, context: list, midas_vectors: list) -> tuple:
        """vectorizes the previous context"""
        embedding = self.__embed(context)
        midas = self.__norm_midas(midas_vectors)
        return self.__get_context_vec(embedding, midas)

    def __embed(self, utterances: list) -> np.ndarray:
        """
        vectorizes a list of N previous utterances using a provided encoder
        input: List[str]
        output: numpy array (len(utterance), embed_dim)
        """
        return self.vectorizer([" ".join(ut) for ut in utterances]).numpy()

    def __norm_midas(self, midas_vectors: list) -> np.ndarray:
        """
        takes midas vectors of all sentences in the utterance
        and returns a vector with max values per midas label
        """
        vecs = np.zeros((len(midas_vectors), len(self.midas2id)))

        for i, vec in enumerate(midas_vectors):
            # get max probability per each midas labels
            vecs[i] = np.max(np.array(vec), axis=0)

        # return normalized
        return vecs

    def __get_context_vec(self, embedding: np.ndarray, midas_vec: np.ndarray) -> np.ndarray:
        """
        concatenates text embeddings with midas vectors
        and one-hot encoded entities

        The output vector will be (n_utterances, self.vector_dim)
        Vector dim comes from:
        1. [embedding of utterance(i-2)]
        2. [midas proba distribution utterance(i-2)]
        4. [embedding (i-1)]
        5. [midas (i-1)][entity (i-1)]
        7. [midas (i)]
        """
        assert embedding.shape[0] == midas_vec.shape[0]

        vecs = np.zeros((self.context_len, self.utterance_vec_size))
        vecs[:, : embedding.shape[1]] = embedding
        vecs[:, embedding.shape[1] :] = midas_vec
        vecs = vecs.reshape(-1)

        assert vecs.shape[0] == self.vector_size

        # returned context vector (1, n_ut * utterance_dim)
        return vecs.reshape(-1)
