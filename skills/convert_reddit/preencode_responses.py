# %%
import logging
import argparse
import pickle
import pathlib
import json

import tqdm
import tensorflow_hub as tfhub
import tensorflow as tf
import tensorflow_text
import numpy as np

tensorflow_text.__name__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler('log.txt'),
    ],
)
logger = logging.getLogger(__name__)

if globals().get("get_ipython"):
    import sys

    sys.argv = [""]
    del sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "--responses_file_path",
    type=pathlib.Path,
    help="Path to the json responses file",
    default="score_filtered_comments.json",
)
parser.add_argument(
    "--store_file_path",
    type=pathlib.Path,
    help="Store to a file of pickle format",
    default="replies.pkl",
)
parser.add_argument("--tfhub_model_dir_path", type=pathlib.Path, help="Path of a tfhub model dir", default="convert")
parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
parser.add_argument("--embedded_key", type=str, default="reply")
parser.add_argument("--associative_value", type=str, default="reply")

args = parser.parse_args()

responses = [
    (req_res.get(args.embedded_key), req_res.get(args.associative_value))
    for req_res in json.load(args.responses_file_path.open())
    if req_res
]
responses = [(key, value) for key, value in responses if key and value]

sess = tf.InteractiveSession(graph=tf.Graph())

module = tfhub.Module(str(args.tfhub_model_dir_path))
text_placeholder = tf.placeholder(dtype=tf.string, shape=[None])

response_encoding_tensor = module(text_placeholder, signature="encode_response")

sess.run(tf.tables_initializer())
sess.run(tf.global_variables_initializer())


def encode_responses(texts):
    return sess.run(response_encoding_tensor, feed_dict={text_placeholder: texts})


keys, values = list(zip(*responses))
key_encodings = []
for i in tqdm.tqdm(range(0, len(keys), args.batch_size)):
    batch = keys[i : i + args.batch_size]
    key_encodings.append(encode_responses(batch))

key_encodings = np.concatenate(key_encodings)
logger.info(f"Encoded {key_encodings.shape[0]} candidate responses.")

pickle.dump((key_encodings, values), args.store_file_path.open("wb"))
