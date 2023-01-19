import os
import numpy as np

import tensorflow as tf
import tensorflow_text
import tensorflow_hub as tfhub


tf.compat.v1.disable_eager_execution()
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
CONVERT_MODEL_PATH = os.environ.get("CONVERT_MODEL_PATH", None)


class Encoder:
    def __init__(self):
        self.sess = tf.compat.v1.Session()
        self.text_placeholder = tf.compat.v1.placeholder(dtype=tf.string, shape=[None])

        self.module = tfhub.Module(CONVERT_MODEL_PATH)
        self.context_encoding_tensor = self.module(self.text_placeholder, signature="encode_context")
        self.encoding_tensor = self.module(self.text_placeholder)
        self.response_encoding_tensor = self.module(self.text_placeholder, signature="encode_response")

        self.sess.run(tf.compat.v1.tables_initializer())
        self.sess.run(tf.compat.v1.global_variables_initializer())

    def encode_sentences(self, sentences):
        vectors = self.sess.run(self.encoding_tensor, feed_dict={self.text_placeholder: sentences})
        return self.__normalize_vectors(vectors)

    def encode_contexts(self, sentences):
        vectors = self.sess.run(self.context_encoding_tensor, feed_dict={self.text_placeholder: sentences})
        return self.__normalize_vectors(vectors)

    def encode_responses(self, sentences):
        vectors = self.sess.run(self.response_encoding_tensor, feed_dict={self.text_placeholder: sentences})
        return self.__normalize_vectors(vectors)

    def __normalize_vectors(self, vectors):
        vectors = np.vstack(vectors)
        norm = np.linalg.norm(vectors, ord=2, axis=-1, keepdims=True)
        return vectors/norm
