import numpy as np
import tensorflow as tf

from tensorflow.keras.utils import Sequence


class SkillDataset(Sequence):
    """ customized Dataset class from torch """

    def __init__(
            self, data: list, vars2id: dict,
            text_vectorizer, label_encoder,
            n_previous: int = 3, embed_dim: int = 512,
            batch_size: int = 32, shuffle: bool = False):

        self.data = data
        self.indexes = np.arange(len(self.data))
        self.vars2id = vars2id
        self.vectorizer = text_vectorizer
        self.label_encoder = label_encoder
        self.n_previous = n_previous
        self.utterance_dim = (
                embed_dim +
                len(vars2id['midas2id']) +
                len(vars2id['entities2id']))

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
        """ get batch_id and return its vectorized representation """
        indexes = self.indexes[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch = [self.data[index] for index in indexes]

        x_batch, y_batch = self.__extract_features(batch)

        return x_batch, y_batch

    def __extract_features(self, batch) -> tuple:
        """
        transaforms raw data into vectorized features and encoded labels
        and collate them into batches
        """
        x_batch = np.zeros([len(batch), self.n_previous * self.utterance_dim])
        y_batch = list()

        for i, sample in enumerate(batch):
            embedding = self.__embed(sample['previous_text'])
            x_midas = self.__norm_midas(sample['midas_vectors'])
            x_entities = self.__oh_encode(sample['previous_entities'])
            x_batch[i, :] = self.__concat_vecs(embedding, x_midas, x_entities)
            y_batch.append(
                (sample['predict']['midas'], sample['predict']['entity']['label'])
            )

        y_batch = self.label_encoder.to_categorical(y_batch)

        return x_batch, y_batch

    def __embed(self, utterances: list) -> np.ndarray:
        """
        vectorizes a list of N previous utterances using a provided encoder

        USE returns Tensors but item assignment is performed downstream,
        thus it is converted to numpy as EagerTensor objects
        do not support item assignment

        input: List[str]
        output: numpy array (len(utterance), embed_dim)
        """
        return self.vectorizer([" ".join(ut) for ut in utterances]).numpy()

    def __norm_midas(self, midas_vectors: list) -> np.ndarray:
        """
        takes midas vectors of all sentences in the utterance
        and returns a vector with max values per midas label
        """
        vecs = np.zeros((len(midas_vectors), 13))

        for i, vec in enumerate(midas_vectors):
            # get max probability per each midas labels
            vecs[i] = np.max(np.array(vec), axis=0)

        # return normalized
        return vecs

    def __oh_encode(self, entities) -> np.ndarray:
        """
        one-hot encoding of entities per each sample

        TODO: replace with sklearn MultiLabelBinarizer
        """
        entities = [[ent['label'] for sent in ut for ent in sent] for ut in entities]
        ohe_vec = np.zeros((len(entities), len(self.vars2id['entities2id'])))

        for i, ut in enumerate(entities):
            for ent in set(ut):
                ohe_vec[i][self.vars2id['entities2id'][ent]] = 1

        return ohe_vec

    def __concat_vecs(self, embedding: tf.Tensor,
                      midas_vec: np.array,
                      ohe_vec: np.array) -> tf.Tensor:
        """
        concatenates text embeddings with midas vectors
        and one-hot encoded entities

        The output vector will be (n_utterances, self.vector_dim)
        Vector dim comes from:
        1. [tfidf utterance(i-2)]
        2. [midas proba distribution utterance(i-2)]
        3. [entity type one-hot utterance(i-2)]
        4. [tfidf (i-1)]
        5. [midas (i-1)][entity (i-1)]
        6. [tfidf (i)]
        7. [midas (i)]
        8. [entity (i)]
        """
        assert embedding.shape[0] == midas_vec.shape[0] == ohe_vec.shape[0]

        vecs = np.zeros((self.n_previous, self.utterance_dim))

        vecs[:, :embedding.shape[1]] = embedding
        vecs[:, embedding.shape[1]:embedding.shape[1] + midas_vec.shape[1]] = midas_vec
        vecs[:, embedding.shape[1] + midas_vec.shape[1]:] = ohe_vec

        # returned one utterance vectors shaped from its sentences
        return tf.reshape(vecs, [-1])
