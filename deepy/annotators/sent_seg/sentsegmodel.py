import os

import helper
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from nltk import word_tokenize
from tensorflow.contrib.layers import xavier_initializer, xavier_initializer_conv2d


class model:
    def __init__(self, params, pretrained_model_path=""):
        self.params = params
        self.pretrained_model_path = pretrained_model_path
        dicts = helper.load_dictionaries(self.params.dicts_file)
        self.word2id = dicts["word2id"]
        self.id2word = dicts["id2word"]
        self.char2id = dicts["char2id"]
        self.id2char = dicts["id2char"]
        self.tag2id = dicts["tag2id"]
        self.id2tag = dicts["id2tag"]

        self.pretrained_emb = np.zeros(shape=(len(self.word2id), self.params.word_dim))
        if self.pretrained_model_path == "" and self.params.train != "" and self.params.pretrained_emb != "":
            self.pretrained_emb = helper.load_word_emb(self.word2id, self.pretrained_emb, self.params.pretrained_emb)

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
            tf_word_embeddings = tf.Variable(
                self.pretrained_emb, dtype=tf.float32, trainable=True, name="word_embedding"
            )
            self.input = tf.nn.embedding_lookup(tf_word_embeddings, self.tf_word_ids, name="embedded_words")

        with tf.variable_scope("char_cnn"):
            tf_char_embeddings = tf.get_variable(
                name="char_embeddings",
                dtype=tf.float32,
                shape=[len(self.char2id), self.params.char_dim],
                trainable=True,
                initializer=xavier_initializer(),
            )
            embedded_cnn_chars = tf.nn.embedding_lookup(tf_char_embeddings, self.tf_char_ids, name="embedded_cnn_chars")
            conv1 = tf.layers.conv2d(
                inputs=embedded_cnn_chars,
                filters=self.params.nb_filters_1,
                kernel_size=(1, 3),
                strides=(1, 1),
                padding="same",
                name="conv1",
                kernel_initializer=xavier_initializer_conv2d(),
            )
            conv2 = tf.layers.conv2d(
                inputs=conv1,
                filters=self.params.nb_filters_2,
                kernel_size=(1, 3),
                strides=(1, 1),
                padding="same",
                name="conv2",
                kernel_initializer=xavier_initializer_conv2d(),
            )
            char_cnn = tf.reduce_max(conv2, axis=2)
            self.input = tf.concat([self.input, char_cnn], axis=-1)

        with tf.variable_scope("elmo_emb"):
            elmo = hub.Module("/elmo2", trainable=False)
            embeddings = elmo(
                inputs={"tokens": self.tf_raw_word, "sequence_len": self.tf_sentence_lengths},
                signature="tokens",
                as_dict=True,
            )[
                "elmo"
            ]  # num_sent, max_sent_len, 1024
            elmo_emb = tf.layers.dense(inputs=embeddings, units=self.params.elmo_dim, activation=None)
            self.input = tf.concat([self.input, elmo_emb], axis=-1)

        self.input = tf.nn.dropout(self.input, self.tf_dropout)

        with tf.variable_scope("bi_lstm_words"):
            cell_fw = tf.contrib.rnn.LSTMCell(self.params.word_hidden_size)
            cell_bw = tf.contrib.rnn.LSTMCell(self.params.word_hidden_size)
            (output_fw, output_bw), _ = tf.nn.bidirectional_dynamic_rnn(
                cell_fw, cell_bw, self.input, sequence_length=self.tf_sentence_lengths, dtype=tf.float32
            )
            self.output = tf.concat([output_fw, output_bw], axis=-1)
            ntime_steps = tf.shape(self.output)[1]
            self.output = tf.reshape(self.output, [-1, 2 * params.word_hidden_size])
            layer1 = tf.nn.dropout(
                tf.layers.dense(
                    inputs=self.output,
                    units=params.word_hidden_size,
                    activation=None,
                    kernel_initializer=xavier_initializer(),
                ),
                self.tf_dropout,
            )
            pred = tf.layers.dense(
                inputs=layer1, units=len(self.tag2id), activation=None, kernel_initializer=xavier_initializer()
            )
            self.logits = tf.reshape(pred, [-1, ntime_steps, len(self.tag2id)])

            # compute loss value using crf
            log_likelihood, self.transition_params = tf.contrib.crf.crf_log_likelihood(
                self.logits, self.tf_labels, self.tf_sentence_lengths
            )
        with tf.variable_scope("loss_and_opt"):
            self.tf_loss = tf.reduce_mean(-log_likelihood)
            optimizer = tf.train.AdamOptimizer(learning_rate=self.tf_learning_rate)
            self.tf_train_op = optimizer.minimize(self.tf_loss)

    def read_raw_data(self, raw_file_path, min_length_of_sentence):
        # return raw_data{word, tag, pos, chunk}
        word, word_, tag, tag_ = [], [], [], []
        nb_part = 2
        lines = open(file=raw_file_path, mode="r", encoding="utf8").readlines()
        for line in lines:
            if line.startswith("-DOCSTART-"):
                continue
            tokens = line.strip().split()
            # end of the sentence
            if len(tokens) == 0:
                if len(word_) < min_length_of_sentence:
                    continue
                word.append(word_)
                tag.append(tag_)
                word_, tag_ = [], []
                continue
            if len(tokens) < nb_part:
                print("* input data is not valid:", line)
                continue
            word_.append(tokens[0])
            tag_.append(tokens[-1])
        raw_data = {"word": word, "tag": tag}
        return raw_data

    def index_data(self, raw_data):
        # input: raw_data{word, tag}
        # output: indexed_data{indexed_word, indexed_char, indexed_tag}
        def low(x):
            return x.lower() if self.params.lower == 1 else x

        def zer(s):
            return helper.zeros(s) if self.params.zeros == 1 else s

        word = [[low(zer(x)) for x in s] for s in raw_data["word"]]
        indexed_word = [[self.word2id[w] if w in self.word2id else self.word2id["<UNK>"] for w in s] for s in word]
        indexed_data = {"indexed_word": indexed_word, "raw_word": raw_data["word"]}
        if "tag" in raw_data:
            indexed_tag = [[self.tag2id[t] for t in s] for s in raw_data["tag"]]
            indexed_data["indexed_tag"] = indexed_tag
        indexed_char = [
            [[self.char2id[c] if c in self.char2id else self.char2id["<UNK>"] for c in zer(w)] for w in s]
            for s in raw_data["word"]
        ]
        indexed_data["indexed_char"] = indexed_char
        return indexed_data

    def get_batch(self, data, start_idx):
        # input: data{indexed_word, indexed_char, indexed_tag, indexed_pos, indexed_chunk}
        # output: a batch of data after padding
        nb_sentences = len(data["indexed_word"])
        end_idx = start_idx + self.params.batch_size
        if end_idx > nb_sentences:
            end_idx = nb_sentences
        batch_word = data["indexed_word"][start_idx:end_idx]
        if "indexed_tag" in data:
            batch_tag = data["indexed_tag"][start_idx:end_idx]
        batch_char = data["indexed_char"][start_idx:end_idx]
        batch_raw_word = data["raw_word"][start_idx:end_idx]
        real_sentence_lengths = [len(sent) for sent in batch_word]
        max_len_sentences = max(real_sentence_lengths)

        padded_word = [
            np.lib.pad(
                sent,
                (0, max_len_sentences - len(sent)),
                "constant",
                constant_values=(self.word2id["<PAD>"], self.word2id["<PAD>"]),
            )
            for sent in batch_word
        ]

        batch = {
            "batch_word": batch_word,
            "padded_word": padded_word,
            "real_sentence_lengths": real_sentence_lengths,
            "padded_raw_word": [sent + [""] * (max_len_sentences - len(sent)) for sent in batch_raw_word],
        }

        if "indexed_tag" in data:
            padded_tag = [
                np.lib.pad(
                    sent,
                    (0, max_len_sentences - len(sent)),
                    "constant",
                    constant_values=(self.tag2id["<PAD>"], self.tag2id["<PAD>"]),
                )
                for sent in batch_tag
            ]
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
                padded_sentence.append(
                    np.lib.pad(
                        word,
                        (0, max_len_of_word - len(word)),
                        "constant",
                        constant_values=(self.char2id["<PAD>"], self.char2id["<PAD>"]),
                    )
                )

            for i in range(max_len_of_sentence - len(padded_sentence)):
                padded_sentence.append(padding_word)
                length_of_word_in_sentence.append(0)

            padded_char.append(padded_sentence)
            lengths_of_word.append(length_of_word_in_sentence)

        lengths_of_word = np.array(lengths_of_word)

        batch["padded_char"] = padded_char
        batch["lengths_of_word"] = lengths_of_word

        return batch, end_idx

    def train(self, training_file_path, val_file_path, output_model_path=None, nb_epochs=20, init_model_path=None):
        raw_train_data = self.read_raw_data(raw_file_path=training_file_path, min_length_of_sentence=2)
        raw_val_data = self.read_raw_data(raw_file_path=val_file_path, min_length_of_sentence=2)

        indexed_train_data = self.index_data(raw_train_data)
        indexed_val_data = self.index_data(raw_val_data)

        saver = tf.train.Saver()
        best_f1 = 0
        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            # reload model
            if self.pretrained_model_path != "":
                print("Model is being reloaded from {:}".format(self.pretrained_model_path))
                saver.restore(sess, self.pretrained_model_path + "/model")
                _, best_f1 = self.evaluate(sess, indexed_val_data)
                print("The best f1: {:06.05}".format(best_f1))

            # train model
            print(self.params)
            for epoch in range(nb_epochs):
                # shuffle data
                random_indexes = np.random.permutation(len(indexed_train_data["indexed_word"]))
                data = {}
                for i in indexed_train_data:
                    data[i] = [indexed_train_data[i][j] for j in random_indexes]

                losses_of_batches = []
                current_idx = 0
                while current_idx < len(data["indexed_word"]):
                    batch, current_idx = self.get_batch(data, current_idx)
                    feed_dict = {
                        self.tf_word_ids: batch["padded_word"],
                        self.tf_sentence_lengths: batch["real_sentence_lengths"],
                        self.tf_labels: batch["padded_tag"],
                        self.tf_learning_rate: self.params.learning_rate,
                        self.tf_dropout: self.params.dropout,
                        self.tf_char_ids: batch["padded_char"],
                        self.tf_word_lengths: batch["lengths_of_word"],
                        self.tf_raw_word: batch["padded_raw_word"],
                    }

                    _, train_loss = sess.run([self.tf_train_op, self.tf_loss], feed_dict=feed_dict)
                    losses_of_batches.append(train_loss)

                mean_loss = np.mean(losses_of_batches)

                # evaluate model on the dev set
                acc, f1 = self.evaluate(sess, indexed_val_data)
                if f1 > best_f1:
                    best_f1 = f1
                    if output_model_path is not None:
                        saver.save(sess, output_model_path)
                        print(
                            "Epoch {:2d}: Train: mean loss: {:.4f} | Val. set: acc: {:.4f}, f1: {:.4f} (*).".format(
                                epoch, mean_loss, acc, f1
                            )
                        )
                    else:
                        print(
                            "Epoch {:2d}: Train: mean loss: {:.4f} | Val. set: acc: {:.4f}, f1: {:.4f} (*).".format(
                                epoch, mean_loss, acc, f1
                            )
                        )
                else:
                    print(
                        "Epoch {:2d}: Train: mean loss: {:.4f} | Val. set: acc: {:.4f}, f1: {:.4f}".format(
                            epoch, mean_loss, acc, f1
                        )
                    )
        print("Training finished.")

    def evaluate(self, sess, data):
        accs = []
        correct_preds, total_correct, total_preds = 0.0, 0.0, 0.0
        current_idx = 0
        while current_idx < len(data["indexed_word"]):
            batch, current_idx = self.get_batch(data, current_idx)
            # decode using Viterbi algorithm
            viterbi_sequences = []
            feed_dict = {
                self.tf_word_ids: batch["padded_word"],
                self.tf_sentence_lengths: batch["real_sentence_lengths"],
                self.tf_dropout: 1.0,
                self.tf_char_ids: batch["padded_char"],
                self.tf_word_lengths: batch["lengths_of_word"],
                self.tf_raw_word: batch["padded_raw_word"],
            }
            _logits, _transition_params = sess.run([self.logits, self.transition_params], feed_dict=feed_dict)

            # iterate over the sentences
            for _logit, sequence_length in zip(_logits, batch["real_sentence_lengths"]):
                # keep only the valid time steps
                _logit = _logit[:sequence_length]
                viterbi_sequence, viterbi_score = tf.contrib.crf.viterbi_decode(_logit, _transition_params)
                viterbi_sequences += [viterbi_sequence]

            for lab, lab_pred in zip(batch["batch_tag"], viterbi_sequences):
                accs += [a == b for (a, b) in zip(lab, lab_pred)]
                lab_chunks = set(helper.get_chunks(lab, self.tag2id))
                lab_pred_chunks = set(helper.get_chunks(lab_pred, self.tag2id))
                correct_preds += len(lab_chunks & lab_pred_chunks)
                total_preds += len(lab_pred_chunks)
                total_correct += len(lab_chunks)

        p = correct_preds / total_preds if correct_preds > 0 else 0
        r = correct_preds / total_correct if correct_preds > 0 else 0
        f1 = 2 * p * r / (p + r) if correct_preds > 0 else 0
        acc = np.mean(accs)
        return acc, f1

    def evaluate_using_conlleval(
        self, model_path, testing_file_path, output_folder, min_length_of_sentence=0, show_score_file=True
    ):
        output_file = os.path.join(output_folder, "result.txt")
        score_file = os.path.join(output_folder, "score.txt")

        raw_data = self.read_raw_data(raw_file_path=testing_file_path, min_length_of_sentence=1)
        indexed_data = self.index_data(raw_data)

        f_out = open(output_file, "w", encoding="utf8")
        saver = tf.train.Saver()
        with tf.Session() as sess:
            saver.restore(sess, model_path)
            current_idx = 0
            while current_idx < len(indexed_data["indexed_word"]):
                batch, current_idx = self.get_batch(indexed_data, current_idx)

                # decode using Viterbi algorithm
                viterbi_sequences = []
                feed_dict = {
                    self.tf_word_ids: batch["padded_word"],
                    self.tf_sentence_lengths: batch["real_sentence_lengths"],
                    self.tf_dropout: 1.0,
                    self.tf_char_ids: batch["padded_char"],
                    self.tf_word_lengths: batch["lengths_of_word"],
                    self.tf_raw_word: batch["padded_raw_word"],
                }
                _logits, _transition_params = sess.run([self.logits, self.transition_params], feed_dict=feed_dict)

                # iterate over the sentences
                for _logit, sequence_length in zip(_logits, batch["real_sentence_lengths"]):
                    # keep only the valid time steps
                    _logit = _logit[:sequence_length]
                    viterbi_sequence, viterbi_score = tf.contrib.crf.viterbi_decode(_logit, _transition_params)
                    viterbi_sequences += [viterbi_sequence]

                for words, labs, lab_preds in zip(batch["batch_word"], batch["batch_tag"], viterbi_sequences):
                    for word, lab, lab_pred in zip(words, labs, lab_preds):
                        f_out.write("{:} {:} {:}\n".format(self.id2word[word], self.id2tag[lab], self.id2tag[lab_pred]))
                    f_out.write("\n")

        f_out.close()
        os.system('perl "%s" < "%s" > "%s"' % ("conlleval", output_file, score_file))
        print("Tagging output and testing results were written to " + output_file + " and " + score_file)

        if show_score_file:
            print("Score on {} calculated by ConllEval:".format(testing_file_path))
            f_in = open(score_file, mode="r", encoding="utf8")
            for line in f_in.readlines():
                print(line)

    def predict(self, sess, text):
        inp_sent = text

        if inp_sent == "":
            return ""

        for p in [".", "?", "!"]:
            if p in inp_sent:
                return inp_sent

        words = word_tokenize(inp_sent)

        raw_data = {"word": [words]}

        indexed_data = self.index_data(raw_data)

        current_idx = 0
        while current_idx < len(indexed_data["indexed_word"]):
            batch, current_idx = self.get_batch(indexed_data, current_idx)

            # decode using Viterbi algorithm
            viterbi_sequences = []
            feed_dict = {
                self.tf_word_ids: batch["padded_word"],
                self.tf_sentence_lengths: batch["real_sentence_lengths"],
                self.tf_dropout: 1.0,
                self.tf_char_ids: batch["padded_char"],
                self.tf_word_lengths: batch["lengths_of_word"],
                self.tf_raw_word: batch["padded_raw_word"],
            }
            _logits, _transition_params = sess.run([self.logits, self.transition_params], feed_dict=feed_dict)

            # iterate over the sentences
            for _logit, sequence_length in zip(_logits, batch["real_sentence_lengths"]):
                # keep only the valid time steps
                _logit = _logit[:sequence_length]
                viterbi_sequence, viterbi_score = tf.contrib.crf.viterbi_decode(_logit, _transition_params)
                viterbi_sequences += [viterbi_sequence]

            # pred_labels = [[self.id2tag[t] for t in s] for s in viterbi_sequences]
            pred_labels = [self.id2tag[t] for t in viterbi_sequences[0]]
            # print("Pred_labels: ",pred_labels)

            tag2text = {"B-S": ".", "B-Q": "?", "O": "."}

            punctuation = tag2text[pred_labels[0]]
            sent = words[0]

            for word, tag in zip(words[1:], pred_labels[1:]):
                if tag != "O":
                    sent += punctuation
                    punctuation = tag2text[tag]
                sent += " " + word
            sent += punctuation

            return sent
