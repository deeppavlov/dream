import os
import helper
import tensorflow as tf
import numpy as np
from tensorflow.contrib.layers import xavier_initializer, xavier_initializer_conv2d
import pickle

import nltk
try:
	nltk.data.find('tokenizers/punkt')
except LookupError:
	nltk.download('punkt')

from nltk.tokenize import word_tokenize

class model:
	def __init__(self, params, pretrained_model_path=""):
		self.params = params
		self.pretrained_model_path = pretrained_model_path
		self.nb_caps = 5

		dicts = helper.load_dictionaries(self.params.dicts_file)
		self.word2id = dicts["word2id"]
		self.id2word = dicts["id2word"]
		if self.params.use_char_cnn:
			self.char2id = dicts["char2id"]
			self.id2char = dicts["id2char"]

		self.tag2id = dicts["tag2id"]
		self.id2tag = dicts["id2tag"]
		if self.params.use_pos == 1:
			self.pos2id = dicts["pos2id"]
			self.id2pos = dicts["id2pos"]
		if self.params.use_chunk == 1:
			self.chunk2id = dicts["chunk2id"]
			self.id2chunk = dicts["id2chunk"]

		self.pretrained_emb = np.zeros(shape=(len(self.word2id), self.params.word_dim))		

		# build model
		tf.reset_default_graph()
		self.tf_word_ids = tf.placeholder(dtype=tf.int32, shape=[None, None], name="word_ids")
		self.tf_sentence_lengths = tf.placeholder(dtype=tf.int32, shape=[None], name="sentence_lengths")
		self.tf_labels = tf.placeholder(dtype=tf.int32, shape=[None, None], name="labels")
		self.tf_dropout = tf.placeholder(dtype=tf.float32, shape=[], name="drop_out")
		self.tf_learning_rate= tf.placeholder(dtype=tf.float32, shape=[], name="learning_rate")

		if self.params.use_char_cnn == 1:
			self.tf_char_ids = tf.placeholder(dtype=tf.int32, shape=[None, None, None], name="char_ids")
			self.tf_word_lengths = tf.placeholder(dtype=tf.int32, shape=[None, None], name="word_lengths")

		if self.params.use_cap == 1:
			self.tf_cap_ids = tf.placeholder(dtype=tf.int32, shape=[None, None], name="cap_ids")

		if self.params.use_pos == 1:
			self.tf_pos_ids = tf.placeholder(dtype=tf.int32, shape=[None, None], name="pos_ids")
		if self.params.use_chunk == 1:
			self.tf_chunk_ids = tf.placeholder(dtype=tf.int32, shape=[None, None], name="chunk_ids")

		if self.params.use_elmo == 1:
			self.tf_raw_word = tf.placeholder(dtype=tf.string, shape=[None, None], name="raw_word")

		with tf.variable_scope("word_embedding"):
			tf_word_embeddings = tf.Variable(self.pretrained_emb, dtype=tf.float32,
				trainable=True, name="word_embedding")
			self.input = tf.nn.embedding_lookup(tf_word_embeddings, self.tf_word_ids, name="embedded_words")

			if self.params.use_pos == 1:
				tf_pos_embeddings = tf.get_variable(name="pos_embeddings",
												 dtype=tf.float32,
												 shape=[len(self.pos2id), self.params.pos_dim],
												 trainable=True,
												 initializer = xavier_initializer())

				embedded_pos = tf.nn.embedding_lookup(tf_pos_embeddings,
															self.tf_pos_ids,
															name="embedded_pos")
				self.input = tf.concat([self.input, embedded_pos], axis=-1)

			if self.params.use_chunk == 1:
				tf_chunk_embeddings = tf.get_variable(name="chunk_embeddings",
												 dtype=tf.float32,
												 shape=[len(self.chunk2id), self.params.chunk_dim],
												 trainable=True,
												 initializer = xavier_initializer())

				embedded_chunk = tf.nn.embedding_lookup(tf_chunk_embeddings,
															self.tf_chunk_ids,
															name="embedded_chunk")
				self.input = tf.concat([self.input, embedded_chunk], axis=-1)

		if self.params.use_char_cnn == 1:
			with tf.variable_scope("char_cnn"):
				if self.params.pretrained_char_emb is not None and self.params.pretrained_char_emb != "":
					print("Initialize char embedding ..")
					tf_char_embeddings = tf.Variable(self.pretrained_char_emb, dtype=tf.float32,
						trainable=True, name="char_embedding")
				else:
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

		if self.params.use_cap == 1:
			with tf.variable_scope("cap_bilstm"):
				cap_embeddings = tf.get_variable(name="cap_embeddings", dtype=tf.float32, shape=[self.nb_caps, self.params.cap_dim],
										 trainable=True, initializer=xavier_initializer())
				ebedded_caps = tf.nn.embedding_lookup(cap_embeddings, self.tf_cap_ids, name="ebedded_caps")
				# cap_cell_fw = tf.contrib.rnn.LSTMCell(self.params.cap_hidden_size)
				# cap_cell_bw = tf.contrib.rnn.LSTMCell(self.params.cap_hidden_size)
				# (cap_output_fw, cap_output_bw), _ = tf.nn.bidirectional_dynamic_rnn(cap_cell_fw,
				# 																	cap_cell_bw, ebedded_caps,
				# 																	sequence_length=self.tf_sentence_lengths,
				# 																	dtype=tf.float32)
				# cap_output = tf.concat([cap_output_fw, cap_output_bw], axis=-1)
				
				# self.input = tf.concat([self.input, cap_output], axis=-1)
				self.input = tf.concat([self.input, ebedded_caps], axis=-1)		
				
		self.input = tf.nn.dropout(self.input, self.tf_dropout)
		
		with tf.variable_scope("bi_lstm_words"):
			cell_fw = tf.contrib.rnn.LSTMCell(self.params.word_hidden_size)
			cell_bw = tf.contrib.rnn.LSTMCell(self.params.word_hidden_size)
			(output_fw, output_bw), _ = tf.nn.bidirectional_dynamic_rnn(cell_fw, cell_bw, self.input,
																		sequence_length=self.tf_sentence_lengths,
																		dtype=tf.float32)
			self.output = tf.concat([output_fw, output_bw], axis=-1)

			if self.params.use_attention == 1:
				self.output = tf.nn.dropout(self.output, self.tf_dropout)
				# print("bi-lstm output:", self.output)
				self.nb_words = tf.shape(output_fw)[1]

				with tf.variable_scope("attention"):
					d = tf.tile(tf.expand_dims(self.output, 1), (1, self.nb_words, 1, 1))
					# print("d (expand_dims and tile): ",d)
					f = tf.tile(tf.expand_dims(self.output, 2), (1, 1, self.nb_words, 1))
					# print("f (expand_dims and tile:",f)
					i = tf.concat([d, f], 3)

					self.output = tf.reduce_sum(i, axis=2)
					
					# j = tf.layers.dense(inputs=i,
					# 					units=256, # dimenson of attention layer
					# 					activation=None, # Linear activation
					# 					kernel_initializer=xavier_initializer()) #, self.tf_dropout)
					# print("j (dense 256):", j)
					
					# # CNN
					# # conv3 = tf.layers.conv2d(inputs=j,
					# # 						 filters=100,
					# # 						 kernel_size=(3, 3),
					# # 						 strides=(1, 1),
					# # 						 padding="same",
					# # 						 kernel_initializer=xavier_initializer_conv2d(),
					# # 						 name="conv3")
					# # conv4 = tf.layers.conv2d(inputs=conv3,
					# # 						 filters=100,
					# # 						 kernel_size=(3, 3),
					# # 						 strides=(1, 1),
					# # 						 padding="same",
					# # 						 kernel_initializer=xavier_initializer_conv2d(),
					# # 						 name="conv4")

					# k = tf.nn.dropout(tf.layers.dense(inputs=j, #tf.concat([conv3, conv4], axis=-1),
					# # k = tf.nn.dropout(tf.layers.dense(inputs=conv4,
					# 								  units=1,
					# 								  activation=None, #tf.tanh,
					# 								  kernel_initializer=xavier_initializer()), self.tf_dropout)
					# print("k (dense 1):", k)
					# l = tf.squeeze(k)
					# print("l (squeeze) :", l)
					# m = tf.nn.softmax(l, dim=-1)
					# print("m (softmax):", m)
					# n = tf.expand_dims(m, -1)
					# print("n (expand_dims): ", n)
					# q = n * f
					# print("q (n * f):", q)		  
					# att_output = tf.reduce_sum(q, axis=2)
					# print("att_out:", att_output)
					
					# output = att_output
				

				# with tf.variable_scope("attention"):
				# 	x = self.output
				# 	# q = tf.placeholder(dtype=tf.float32, shape=[dq, 1])
				# 	de = x.get_shape()[-1]
				# 	w = tf.get_variable(dtype=tf.float32, shape=[de], trainable=True, name="w")
				# 	w1 = tf.get_variable(dtype=tf.float32, shape=[de, de], trainable=True, name="W1")
				# 	w2 = tf.get_variable(dtype=tf.float32, shape=[de, de], trainable=True, name="W2")
				# 	b1 = tf.get_variable(dtype=tf.float32, shape=[de], trainable=True, name="b1")
				# 	b = tf.get_variable(dtype=tf.float32, shape=[], trainable=True, name="b")

				# 	e1 = tf.transpose(tf.tensordot(x, w1, axes=1), [1,0,2]) #b, n, de -> n, b, de = n, [b,de]
				# 	# print('e1', e1)
				# 	e2 = tf.transpose(tf.tensordot(x, w2, axes=1), [1,0,2]) #b, n, de -> n, b, de
				# 	# print('e2', e2)
				# 	# tong = tf.map_fn(lambda i: i+ e2, e1)#
				# 	tong = tf.transpose(tf.map_fn(lambda i: i + e2 + b1, e1), [2,0,1,3]) # b, n, n, de
				# 	# print('tong', tong)

				# 	weight = tf.tensordot(tf.tanh(tong), w, axes=1) + b # b, n, n
				# 	# print('weight:', weight)
				# 	self.output = tf.transpose(tf.map_fn(lambda y: y*x,tf.expand_dims(tf.transpose(weight, [1,0,2]), -1)), [1,0,2,3])
				# 	self.output = tf.reduce_sum(self.output, axis=2)
		
			ntime_steps = tf.shape(self.output)[1]
			self.output = tf.reshape(self.output, [-1, 2*params.word_hidden_size])
			# output = tf.reshape(output, [-1, 4*params.word_hidden_size])
			layer1 = tf.nn.dropout(tf.layers.dense(inputs=self.output, units=params.word_hidden_size, activation=None, kernel_initializer=xavier_initializer()), self.tf_dropout)
			pred = tf.layers.dense(inputs=layer1, units=len(self.tag2id), activation=None, kernel_initializer=xavier_initializer())
			self.logits = tf.reshape(pred, [-1, ntime_steps, len(self.tag2id)])

			# compute loss value using crf
			log_likelihood, self.transition_params = tf.contrib.crf.crf_log_likelihood(self.logits,
																					   self.tf_labels,
																					   self.tf_sentence_lengths)
		with tf.variable_scope("loss_and_opt"):
			self.tf_loss = tf.reduce_mean(-log_likelihood)
			optimizer = tf.train.AdamOptimizer(learning_rate=self.tf_learning_rate)
			self.tf_train_op = optimizer.minimize(self.tf_loss)

	def read_raw_data(self, raw_file_path, min_length_of_sentence):
		# return raw_data{word, tag, pos, chunk}
		word, word_, tag, tag_ = [], [], [], []
		nb_part = 2
		if self.params.use_pos == 1:
			pos, pos_ = [], []
			nb_part += 1
		if self.params.use_chunk == 1:
			chunk, chunk_ = [], []
			nb_part += 1

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
				if self.params.use_pos == 1:
					pos.append(pos_)
					pos_ = []
				if self.params.use_chunk == 1:
					chunk.append(chunk_)
					chunk_ = []
				continue

			if len(tokens) < nb_part:
				print("* input data is not valid:", line)
				continue

			word_.append(tokens[0])
			tag_.append(tokens[-1])
			if self.params.use_chunk == 1:
				chunk_.append(tokens[-2])
			if self.params.use_pos == 1:
				pos_.append(tokens[-3])

		raw_data = {"word": word, "tag": tag}
		if self.params.use_pos == 1:
			raw_data["pos"] = pos
		if self.params.use_chunk == 1:
			raw_data["chunk"] = chunk

		return raw_data

	def index_data(self, raw_data):
		# input: raw_data{word, tag, pos, chunk}
		# output: indexed_data{indexed_word, indexed_char, indexed_tag, indexed_pos, indexed_chunk, indexed_cap}
		def l(x): return x.lower() if self.params.lower == 1 else x
		def z(s): return helper.zeros(s) if self.params.zeros == 1 else s
		def cap_feature(s):
			if s.upper() == s:
				return 1
			elif s.lower() == s:
				return 2
			elif (s[0].upper() == s[0]) and (s[1:].lower() == s[1:]):
				return 3
			else:
				return 4

		word = [[l(z(x)) for x in s] for s in raw_data["word"]]
		indexed_word = [[self.word2id[w] if w in self.word2id else self.word2id["<UNK>"] for w in s] for s in word]
		indexed_data = {"indexed_word": indexed_word}

		if self.params.use_elmo == 1:
			indexed_data["raw_word"] = raw_data["word"]

		if "tag" in raw_data:
			indexed_tag = [[self.tag2id[t] for t in s] for s in raw_data["tag"]]
			indexed_data["indexed_tag"] = indexed_tag
		
		if self.params.use_char_cnn == 1:
			indexed_char = [[[self.char2id[c] if c in self.char2id else self.char2id["<UNK>"] for c in z(w)] for w in s] for s in raw_data["word"]]
			indexed_data["indexed_char"] = indexed_char
		if self.params.use_pos == 1:
			indexed_pos = [[self.pos2id[p] for p in s] for s in raw_data["pos"]]
			indexed_data["indexed_pos"] = indexed_pos
		if self.params.use_chunk == 1:
			indexed_chunk = [[self.chunk2id[c] for c in s] for s in raw_data["chunk"]]
			indexed_data["indexed_chunk"] = indexed_chunk
		if self.params.use_cap == 1:
			indexed_cap = [[cap_feature(w) for w in s] for s in raw_data["word"]]
			indexed_data["indexed_cap"] = indexed_cap
		return indexed_data

	def get_batch(self, data, start_idx):
		# input: data{indexed_word, indexed_char, indexed_tag, indexed_pos, indexed_chunk}
		# output: a batch of data after padding
		nb_sentences = len(data["indexed_word"])
		end_idx = start_idx + self.params.batch_size
		if end_idx > nb_sentences:
			end_idx = nb_sentences
		batch_word = data["indexed_word"][start_idx : end_idx]
		if "indexed_tag" in data:
			batch_tag = data["indexed_tag"][start_idx : end_idx]			
		if self.params.use_char_cnn == 1:
			batch_char = data["indexed_char"][start_idx: end_idx]
		if self.params.use_cap == 1:
			batch_cap = data["indexed_cap"][start_idx: end_idx]			
		if self.params.use_pos == 1:
			batch_pos = data["indexed_pos"][start_idx: end_idx]
		if self.params.use_chunk == 1:
			batch_chunk = data["indexed_chunk"][start_idx: end_idx]
		if self.params.use_elmo == 1:
			batch_raw_word = data["raw_word"][start_idx: end_idx]	

		real_sentence_lengths = [len(sent) for sent in batch_word]
		max_len_sentences = max(real_sentence_lengths)
		padded_word = [np.lib.pad(sent, (0, max_len_sentences - len(sent)), 'constant',
			constant_values=(self.word2id["<PAD>"], self.word2id["<PAD>"])) for sent in batch_word]

		batch = {"batch_word": batch_word, "padded_word": padded_word, "real_sentence_lengths": real_sentence_lengths}

		# pad raw text for creating elmo emb
		if self.params.use_elmo == 1:
			batch["padded_raw_word"] = [sent + [''] * (max_len_sentences - len(sent)) for sent in batch_raw_word]

		if "indexed_tag" in data:		
			padded_tag = [np.lib.pad(sent, (0, max_len_sentences - len(sent)), 'constant',
				constant_values=(self.tag2id["<PAD>"], self.tag2id["<PAD>"])) for sent in batch_tag]
			batch["padded_tag"] = padded_tag
			batch["batch_tag"] = batch_tag

		# pad chars
		if self.params.use_char_cnn == 1:
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

		# pad pos
		if self.params.use_pos == 1:
			padded_pos = [np.lib.pad(x, (0, max_len_sentences - len(x)), 'constant',
							   constant_values=(self.pos2id["<PAD>"], self.pos2id["<PAD>"])) for x in batch_pos]
			batch["padded_pos"] = padded_pos
		# pad chunk
		if self.params.use_chunk == 1:
			padded_chunk = [np.lib.pad(x, (0, max_len_sentences - len(x)), 'constant',
						   constant_values=(self.chunk2id["<PAD>"], self.chunk2id["<PAD>"])) for x in batch_chunk]
			batch["padded_chunk"] = padded_chunk
		# pad cap
		if self.params.use_cap == 1:
			padded_cap = [np.lib.pad(x, (0, max_len_sentences - len(x)), 'constant',
								 constant_values=(0, 0)) for x in batch_cap]
			batch["padded_cap"] = padded_cap		

		return batch, end_idx

	def train(self, training_file_path, val_file_path, output_model_path=None, nb_epochs=20, init_model_path=None):
		raw_train_data = self.read_raw_data(raw_file_path=training_file_path, min_length_of_sentence=2)
		raw_val_data = self.read_raw_data(raw_file_path=val_file_path, min_length_of_sentence=2)

		# for k in raw_train_data:
		# 	raw_train_data[k] = raw_train_data[k][:6]
		# for k in raw_val_data:
		# 	raw_val_data[k] = raw_val_data[k][:6]

		# print(raw_train_data)
		# print(raw_val_data)

		indexed_train_data = self.index_data(raw_train_data)
		indexed_val_data = self.index_data(raw_val_data)

		# print(indexed_train_data)
		# print(indexed_val_data)


		saver = tf.train.Saver()
		best_f1 = 0
		with tf.Session() as sess:
			sess.run(tf.global_variables_initializer())
			# reload model
			if self.pretrained_model_path != "":
				print("Model is being reloaded from {:}".format(self.pretrained_model_path))
				saver.restore(sess, self.pretrained_model_path+"/model")
				_, best_f1 = self.evaluate(sess, indexed_val_data)
				print("The best f1: {:06.05}".format(best_f1))

			# train model
			print(self.params)
			for epoch in range(nb_epochs):
				# shuffle data
				random_indexes = np.random.permutation(len(indexed_train_data["indexed_word"]))
				
				# print(random_indexes)

				data = {}
				for i in indexed_train_data:
					data[i] = [indexed_train_data[i][j] for j in random_indexes]

				# print(data)
				# print('='*30)
				losses_of_batches = []
				current_idx = 0
				while current_idx < len(data["indexed_word"]):
					batch, current_idx = self.get_batch(data, current_idx)
					# print("*"*30)
					# print(batch)

					feed_dict = {self.tf_word_ids: batch["padded_word"],
								   self.tf_sentence_lengths: batch["real_sentence_lengths"],
								   self.tf_labels: batch["padded_tag"],								   
								   self.tf_learning_rate: self.params.learning_rate,
								   self.tf_dropout: self.params.dropout}

					if self.params.use_char_cnn == 1:
						feed_dict[self.tf_char_ids] = batch["padded_char"]
						feed_dict[self.tf_word_lengths] = batch["lengths_of_word"]
					if self.params.use_pos == 1:
						feed_dict[self.tf_pos_ids] = batch["padded_pos"]
					if self.params.use_chunk == 1:
						feed_dict[self.tf_chunk_ids] = batch["padded_chunk"]
					if self.params.use_cap == 1:
						feed_dict[self.tf_cap_ids] = batch["padded_cap"]
					if self.params.use_elmo == 1:
						feed_dict[self.tf_raw_word] = batch["padded_raw_word"]
					_, train_loss = sess.run([self.tf_train_op, self.tf_loss], feed_dict=feed_dict)
					losses_of_batches.append(train_loss)

				mean_loss = np.mean(losses_of_batches)

				# evaluate model on the dev set
				acc, f1 = self.evaluate(sess, indexed_val_data)
				if f1 > best_f1:
					best_f1 = f1
					if output_model_path is not None:
						saver.save(sess, output_model_path)
						print ("Epoch {:2d}: Train: mean loss: {:.4f} | Val. set: acc: {:.4f}, f1: {:.4f} (*).".format (epoch, mean_loss, acc, f1))
					else:
						print ("Epoch {:2d}: Train: mean loss: {:.4f} | Val. set: acc: {:.4f}, f1: {:.4f} (*)."
							   .format (epoch, mean_loss, acc, f1))
				else:
					print("Epoch {:2d}: Train: mean loss: {:.4f} | Val. set: acc: {:.4f}, f1: {:.4f}".format(epoch, mean_loss, acc, f1))
		print("Training finished.")

	def evaluate(self, sess, data):
		accs = []
		correct_preds, total_correct, total_preds = 0., 0., 0.
		current_idx = 0
		while current_idx < len(data["indexed_word"]):
			batch, current_idx = self.get_batch(data, current_idx)
			# decode using Viterbi algorithm
			viterbi_sequences = []
			feed_dict = {self.tf_word_ids: batch["padded_word"],
						self.tf_sentence_lengths: batch["real_sentence_lengths"],						
						self.tf_dropout: 1.0}
			if self.params.use_char_cnn == 1:
				feed_dict[self.tf_char_ids] = batch["padded_char"]
				feed_dict[self.tf_word_lengths] = batch["lengths_of_word"]
			if self.params.use_pos == 1:
				feed_dict[self.tf_pos_ids] = batch["padded_pos"]
			if self.params.use_chunk == 1:
				feed_dict[self.tf_chunk_ids] = batch["padded_chunk"]
			if self.params.use_cap == 1:
						feed_dict[self.tf_cap_ids] = batch["padded_cap"]
			if self.params.use_elmo == 1:
						feed_dict[self.tf_raw_word] = batch["padded_raw_word"]
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

	def evaluate_using_conlleval(self, model_path, testing_file_path, output_folder,
								 min_length_of_sentence=0, show_score_file=True):	   
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
				feed_dict = {self.tf_word_ids: batch["padded_word"],
						self.tf_sentence_lengths: batch["real_sentence_lengths"],						
						self.tf_dropout: 1.0}
				if self.params.use_char_cnn == 1:
					feed_dict[self.tf_char_ids] = batch["padded_char"]
					feed_dict[self.tf_word_lengths] = batch["lengths_of_word"]
				if self.params.use_pos == 1:
					feed_dict[self.tf_pos_ids] = batch["padded_pos"]
				if self.params.use_chunk == 1:
					feed_dict[self.tf_chunk_ids] = batch["padded_chunk"]
				if self.params.use_cap == 1:
						feed_dict[self.tf_cap_ids] = batch["padded_cap"]
				if self.params.use_elmo == 1:
						feed_dict[self.tf_raw_word] = batch["padded_raw_word"]
				_logits, _transition_params = sess.run([self.logits, self.transition_params], feed_dict=feed_dict)

				# iterate over the sentences
				for _logit, sequence_length in zip(_logits, batch["real_sentence_lengths"]):
					# keep only the valid time steps
					_logit = _logit[:sequence_length]
					viterbi_sequence, viterbi_score = tf.contrib.crf.viterbi_decode(_logit, _transition_params)
					viterbi_sequences += [viterbi_sequence]

				for words, labs, lab_preds in zip(batch["batch_word"], batch["batch_tag"], viterbi_sequences):
					for word, lab, lab_pred in zip(words, labs, lab_preds):
						f_out.write("{:} {:} {:}\n".format(self.id2word[word],
														   self.id2tag[lab],
														   self.id2tag[lab_pred]))
					f_out.write("\n")

		f_out.close()
		os.system("perl \"%s\" < \"%s\" > \"%s\"" % ("conlleval", output_file, score_file))
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

			
			for p in ['.', '?', '!']:
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
				feed_dict = {self.tf_word_ids: batch["padded_word"],
						self.tf_sentence_lengths: batch["real_sentence_lengths"],						
						self.tf_dropout: 1.0}
				if self.params.use_char_cnn == 1:
					feed_dict[self.tf_char_ids] = batch["padded_char"]
					feed_dict[self.tf_word_lengths] = batch["lengths_of_word"]
				if self.params.use_pos == 1:
					feed_dict[self.tf_pos_ids] = batch["padded_pos"]
				if self.params.use_chunk == 1:
					feed_dict[self.tf_chunk_ids] = batch["padded_chunk"]
				if self.params.use_cap == 1:
						feed_dict[self.tf_cap_ids] = batch["padded_cap"]
				if self.params.use_elmo == 1:
					feed_dict[self.tf_raw_word] = batch["padded_raw_word"]
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

				tag2text = {"B-S": ".", "B-Q": "?", "O": ".", "B-E": "!"}
				
				punctuation = tag2text[pred_labels[0]]
				sent = words[0]

				for word, tag in zip(words[1:], pred_labels[1:]):
					if tag != "O":
						sent += punctuation
						punctuation = tag2text[tag]
					sent += (" " + word)
				sent += punctuation
				
				return sent
