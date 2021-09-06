# tensorflow==1.14.0
# tensorflow_text==0.1.0
# tensorflow-hub==0.7.0
# wget http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.8.tar.gz
# tar xzfv .....
# MODEL_PATH=........../convert_data/convert
import logging
import os

import numpy as np
import sentry_sdk
import tensorflow_hub as tfhub
import tensorflow as tf
import tensorflow_text


sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

tensorflow_text.__name__

MODEL_PATH = "/convert/convert"

sess = tf.InteractiveSession(graph=tf.Graph())

module = tfhub.Module(MODEL_PATH)


text_placeholder = tf.placeholder(dtype=tf.string, shape=[None])
extra_text_placeholder = tf.placeholder(dtype=tf.string, shape=[None])

# The encode_context signature now also takes the extra context.
context_encoding_tensor = module(
    {"context": text_placeholder, "extra_context": extra_text_placeholder}, signature="encode_context"
)


responce_text_placeholder = tf.placeholder(dtype=tf.string, shape=[None])

response_encoding_tensor = module(responce_text_placeholder, signature="encode_response")

sess.run(tf.tables_initializer())
sess.run(tf.global_variables_initializer())


def encode_contexts(dialog_history_batch):
    """Encode the dialog context to the response ranking vector space.

    Args:
        dialog_history_batch: a list of strings, the dialog history, in
            chronological order.
    """

    # The context is the most recent message in the history.
    contexts = []
    extra_context_features = []

    for dialog_history in dialog_history_batch:
        contexts += [dialog_history[-1]]

        extra_context = list(dialog_history[:-1])
        extra_context.reverse()
        extra_context_features += [" ".join(extra_context)]

    return sess.run(
        context_encoding_tensor,
        feed_dict={text_placeholder: contexts, extra_text_placeholder: extra_context_features},
    )


def encode_responses(texts):
    return sess.run(response_encoding_tensor, feed_dict={responce_text_placeholder: texts})


def get_convert_score(contexts, responses):
    context_encodings = encode_contexts(contexts)
    response_encodings = encode_responses(responses)  # 79, 512
    res = np.multiply(context_encodings, response_encodings)
    return np.sum(res, axis=1).reshape(-1, 1)
