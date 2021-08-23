import json
import pickle

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.contrib.layers import xavier_initializer, xavier_initializer_conv2d


class model:
    def __init__(self, params, pretrained_model_path=""):
        self.params = params
        self.pretrained_model_path = pretrained_model_path
        dicts = pickle.load(open(self.params.dicts_file, mode="rb"))
        self.word2id = dicts["word2id"]
        self.id2word = dicts["id2word"]
        self.char2id = dicts["char2id"]
        self.id2char = dicts["id2char"]
        self.tag2id = dicts["tag2id"]
        self.id2tag = dicts["id2tag"]

        self.pretrained_emb = np.zeros(shape=(len(self.word2id), self.params.word_dim))

        # build model
        self.tf_word_ids = tf.placeholder(dtype=tf.int32, shape=[None, None], name="word_ids")
        self.tf_sentence_lengths = tf.placeholder(dtype=tf.int32, shape=[None], name="sentence_lengths")
        self.tf_labels = tf.placeholder(dtype=tf.int32, shape=[None, None], name="labels")
        self.tf_dropout = tf.placeholder(dtype=tf.float32, shape=[], name="drop_out")
        self.tf_learning_rate = tf.placeholder(dtype=tf.float32, shape=[], name="learning_rate")
        self.tf_char_ids = tf.placeholder(dtype=tf.int32, shape=[None, None, None], name="char_ids")
        self.tf_word_lengths = tf.placeholder(dtype=tf.int32, shape=[None, None], name="word_lengths")
        self.tf_raw_word = tf.placeholder(dtype=tf.string, shape=[None, None], name="raw_word")

        with tf.variable_scope("word_embedding"):
            tf_word_embeddings = tf.Variable(self.pretrained_emb, dtype=tf.float32,
                                             trainable=True, name="word_embedding")
            self.input = tf.nn.embedding_lookup(tf_word_embeddings, self.tf_word_ids, name="embedded_words")

        with tf.variable_scope("char_cnn"):
            tf_char_embeddings = tf.get_variable(name="char_embeddings",
                                                 dtype=tf.float32,
                                                 shape=[len(self.char2id), self.params.char_dim],
                                                 trainable=True,
                                                 initializer=xavier_initializer())
            embedded_cnn_chars = tf.nn.embedding_lookup(tf_char_embeddings,
                                                        self.tf_char_ids,
                                                        name="embedded_cnn_chars")
            conv1 = tf.layers.conv2d(inputs=embedded_cnn_chars,
                                     filters=self.params.nb_filters_1,
                                     kernel_size=(1, 3),
                                     strides=(1, 1),
                                     padding="same",
                                     name="conv1",
                                     kernel_initializer=xavier_initializer_conv2d())
            conv2 = tf.layers.conv2d(inputs=conv1,
                                     filters=self.params.nb_filters_2,
                                     kernel_size=(1, 3),
                                     strides=(1, 1),
                                     padding="same",
                                     name="conv2",
                                     kernel_initializer=xavier_initializer_conv2d())
            char_cnn = tf.reduce_max(conv2, axis=2)
            self.input = tf.concat([self.input, char_cnn], axis=-1)

        with tf.variable_scope("elmo_emb"):
            elmo = hub.Module("/elmo2", trainable=False)
            embeddings = \
                elmo(inputs={"tokens": self.tf_raw_word, "sequence_len": self.tf_sentence_lengths}, signature="tokens",
                     as_dict=True)["elmo"]  # num_sent, max_sent_len, 1024
            elmo_emb = tf.layers.dense(inputs=embeddings, units=self.params.elmo_dim, activation=None)
            self.input = tf.concat([self.input, elmo_emb], axis=-1)

        self.input = tf.nn.dropout(self.input, self.tf_dropout)

        with tf.variable_scope("bi_lstm_words"):
            cell_fw = tf.contrib.rnn.LSTMCell(self.params.word_hidden_size)
            cell_bw = tf.contrib.rnn.LSTMCell(self.params.word_hidden_size)
            (output_fw, output_bw), _ = tf.nn.bidirectional_dynamic_rnn(cell_fw, cell_bw, self.input,
                                                                        sequence_length=self.tf_sentence_lengths,
                                                                        dtype=tf.float32)
            self.output = tf.concat([output_fw, output_bw], axis=-1)
            ntime_steps = tf.shape(self.output)[1]
            self.output = tf.reshape(self.output, [-1, 2 * params.word_hidden_size])
            layer1 = tf.nn.dropout(tf.layers.dense(inputs=self.output, units=params.word_hidden_size, activation=None,
                                                   kernel_initializer=xavier_initializer()), self.tf_dropout)
            pred = tf.layers.dense(inputs=layer1, units=len(self.tag2id), activation=None,
                                   kernel_initializer=xavier_initializer())
            self.logits = tf.reshape(pred, [-1, ntime_steps, len(self.tag2id)])

            # compute loss value using crf
            log_likelihood, self.transition_params = tf.contrib.crf.crf_log_likelihood(self.logits,
                                                                                       self.tf_labels,
                                                                                       self.tf_sentence_lengths)
        with tf.variable_scope("loss_and_opt"):
            self.tf_loss = tf.reduce_mean(-log_likelihood)
            optimizer = tf.train.AdamOptimizer(learning_rate=self.tf_learning_rate)
            self.tf_train_op = optimizer.minimize(self.tf_loss)

    def set_session(self, sess):
        self.session = sess

    def index_data(self, raw_data):
        # input: raw_data{word, tag}
        # output: indexed_data{indexed_word, indexed_char, indexed_tag}

        word = [[x.lower() for x in s] for s in raw_data["word"]]
        indexed_word = [[self.word2id[w] if w in self.word2id else self.word2id["<UNK>"] for w in s] for s in word]
        indexed_data = {"indexed_word": indexed_word, "raw_word": raw_data["word"]}
        if "tag" in raw_data:
            indexed_tag = [[self.tag2id[t] for t in s] for s in raw_data["tag"]]
            indexed_data["indexed_tag"] = indexed_tag
        indexed_char = [[[self.char2id[c] if c in self.char2id else self.char2id["<UNK>"] for c in w] for w in s]
                        for s in raw_data["word"]]
        indexed_data["indexed_char"] = indexed_char
        return indexed_data

    def get_batch(self, data, start_idx):
        # input: data{indexed_word, indexed_char, indexed_tag, indexed_pos, indexed_chunk}
        # output: a batch of data after padding
        nb_sentences = len(data["indexed_word"])
        end_idx = start_idx + self.params.batch_size
        if end_idx > nb_sentences:
            end_idx = nb_sentences
        batch_word = data["indexed_word"][start_idx: end_idx]
        if "indexed_tag" in data:
            batch_tag = data["indexed_tag"][start_idx: end_idx]
        batch_char = data["indexed_char"][start_idx: end_idx]
        batch_raw_word = data["raw_word"][start_idx: end_idx]
        real_sentence_lengths = [len(sent) for sent in batch_word]
        max_len_sentences = max(real_sentence_lengths)

        padded_word = [np.lib.pad(sent, (0, max_len_sentences - len(sent)), 'constant',
                                  constant_values=(self.word2id["<PAD>"], self.word2id["<PAD>"])) for sent in
                       batch_word]

        batch = {"batch_word": batch_word, "padded_word": padded_word, "real_sentence_lengths": real_sentence_lengths,
                 "padded_raw_word": [sent + [''] * (max_len_sentences - len(sent)) for sent in batch_raw_word]}

        if "indexed_tag" in data:
            padded_tag = [np.lib.pad(sent, (0, max_len_sentences - len(sent)), 'constant',
                                     constant_values=(self.tag2id["<PAD>"], self.tag2id["<PAD>"])) for sent in
                          batch_tag]
            batch["padded_tag"] = padded_tag
            batch["batch_tag"] = batch_tag

        # pad chars
        max_len_of_sentence = max([len(sentence) for sentence in batch_char])
        max_len_of_word = max([max([len(word) for word in sentence]) for sentence in batch_char])

        padding_word = np.full(max_len_of_word, self.char2id["<PAD>"])
        padded_char = []

        lengths_of_word = []

        for sentence in batch_char:
            padded_sentence = []
            length_of_word_in_sentence = []

            for word in sentence:
                length_of_word_in_sentence.append(len(word))
                padded_sentence.append(np.lib.pad(word, (0, max_len_of_word - len(word)), 'constant',
                                                  constant_values=(self.char2id["<PAD>"], self.char2id["<PAD>"])))

            for i in range(max_len_of_sentence - len(padded_sentence)):
                padded_sentence.append(padding_word)
                length_of_word_in_sentence.append(0)

            padded_char.append(padded_sentence)
            lengths_of_word.append(length_of_word_in_sentence)

        lengths_of_word = np.array(lengths_of_word)

        batch["padded_char"] = padded_char
        batch["lengths_of_word"] = lengths_of_word

        return batch, end_idx

    def predict(self, sents):
        sents = [s if len(s) > 0 else ["."] for s in sents]
        raw_data = {"word": sents}
        indexed_data = self.index_data(raw_data)

        pred_lables = []
        current_idx = 0
        while current_idx < len(indexed_data["indexed_word"]):
            batch, current_idx = self.get_batch(indexed_data, current_idx)
            viterbi_sequences = []
            feed_dict = {self.tf_word_ids: batch["padded_word"],
                         self.tf_sentence_lengths: batch["real_sentence_lengths"],
                         self.tf_dropout: 1.0,
                         self.tf_char_ids: batch["padded_char"],
                         self.tf_word_lengths: batch["lengths_of_word"],
                         self.tf_raw_word: batch["padded_raw_word"]}

            _logits, _transition_params = self.session.run([self.logits, self.transition_params], feed_dict=feed_dict)

            # iterate over the sentences
            for _logit, sequence_length in zip(_logits, batch["real_sentence_lengths"]):
                # keep only the valid time steps
                _logit = _logit[:sequence_length]
                viterbi_sequence, viterbi_score = tf.contrib.crf.viterbi_decode(_logit, _transition_params)
                viterbi_sequences += [viterbi_sequence]

            pred_lables += [[self.id2tag[t] for t in s] for s in viterbi_sequences]

        # conver pred_lables to the expected format
        # this just works with iob tagging scheme
        entities = []
        for sent, tags in zip(sents, pred_lables):
            entities.append([])
            start = end = -1
            for i, (word, tag) in enumerate(zip(sent, tags)):
                if tag[0] == "B":
                    if start != -1:
                        entities[-1].append({"start_pos": start, "end_pos": end, "type": tags[start].split('-')[1],
                                             "text": ' '.join(sent[start: end]), "confidence": 1})
                    start = i
                    end = i + 1
                elif tag[0] == "I":
                    end = i + 1
                else:
                    if start != -1:
                        entities[-1].append({"start_pos": start, "end_pos": end, "type": tags[start].split('-')[1],
                                             "text": ' '.join(sent[start: end]), "confidence": 1})
                        start = -1
            if start != -1:
                entities[-1].append(
                    {"start_pos": start, "end_pos": end, "type": tags[start].split('-')[1],
                     "text": ' '.join(sent[start: end]), "confidence": 1})
        return entities


class pars:
    def __init__(self, dict_properties):
        for k, v in dict_properties.items():
            setattr(self, k, v)


def load_model():
    dict_params = json.load(open("/model/config.json"))
    params = pars(dict_params)
    ner = model(params)

    saver = tf.train.Saver()
    sess = tf.Session()
    saver.restore(sess, "/model/model")
    ner.set_session(sess)
    return ner
