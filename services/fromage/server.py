import logging
import json
import os
import time
import re
from fromage import models
from fromage import utils
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import copy
import torch
import sentry_sdk
import torch
from common.constants import CAN_CONTINUE_SCENARIO
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.getenv('FILE_SERVER_URL')

DEFAULT_CONFIDENCE = 1
ZERO_CONFIDENCE = 0.0


try:
    model_dir = './fromage_model'
    model = models.load_fromage(model_dir)
    
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("fromage is set to run on cuda")

    logger.info("fromage is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

def generate_responses(image_path, prompt):
    ret_scale_factor = 0
    inp_image = utils.get_image_from_url(image_path)
    input_prompts = ["What is this image?"]
    if prompt[0] != '':
        input_prompts = prompt
    input_context = [inp_image] 
    text = ''
    for p in input_prompts: # Add Q+A prefixes for prompting. This is helpful for generating dialogue.
        text += 'Q: ' + p + '\nA:'
        model_prompt = input_context + [text]
        model_outputs = model.generate_for_images_and_texts(model_prompt, num_words=32, ret_scale_factor=ret_scale_factor, max_num_rets=0)
        text += ' '.join([s for s in model_outputs if type(s) == str]) + '\n'
        model_outputs[0] = 'FROMAGe:  ' + model_outputs[0]
    return model_outputs


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    sentence = request.json.get("sentences", [])
    prev_img_path = request.json.get("prev_img_path", [])
    logger.info(f'prev_img_path {prev_img_path}')
    image_path = request.json.get("image_paths", [])

    try:
        responses = []
        confidences = []
        attributes = []

        if image_path[0] is not None:
            outputs = generate_responses(image_path[0], sentence)
            responses += outputs
            confidences += [DEFAULT_CONFIDENCE]
            attributes += [{}]
            logging.info(f'response here {responses}')
        else:
            if prev_img_path is None:
                responses += ["""Please send me pic again I have alzheimer's"""]
            outputs = generate_responses(prev_img_path, sentence)
            responses += outputs
            confidences += [DEFAULT_CONFIDENCE]
            attributes += [{}]
            logging.info(f'response not here here {responses}')

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(sentence)
        confidences = [[ZERO_CONFIDENCE]] * len(sentence)
        attributes = [[{}]] * len(sentence)

    total_time = time.time() - st_time
    logger.info(f"fromage exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, attributes)))


# @app.route("/continue", methods=["POST"])
# def continue_last_uttr():
#     st_time = time.time()
#     contexts = request.json.get("human_uttr_histories", [])
#     if len(contexts) == 0:
#         contexts = request.json.get("dialog_contexts", [])

#     try:
#         responses = []
#         for context in contexts:
#             curr_responses = []
#             outputs = generate_responses(context, model)
#             for response in outputs:
#                 curr_responses += [response]
#             responses += [curr_responses]

#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         responses = [[""]] * len(contexts)

#     total_time = time.time() - st_time
#     logger.info(f"fromage continue exec time: {total_time:.3f}s")
#     return jsonify(responses)
