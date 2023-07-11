import logging
import os
import time
from fromage import models
from fromage import utils
import torch
import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")

DEFAULT_CONFIDENCE = 1
ZERO_CONFIDENCE = 0.0

MAX_RESPONCES_ABOUT_PICS = os.environ.get("MAX_RESPONCES_ABOUT_PICS")
MAX_RESPONCES_ABOUT_PICS = int(MAX_RESPONCES_ABOUT_PICS) if MAX_RESPONCES_ABOUT_PICS else MAX_RESPONCES_ABOUT_PICS


try:
    model_dir = "/annotators/fromage/fromage_model"
    model = models.load_fromage(model_dir)

    if torch.cuda.is_available():
        # model.to("cpu")
        logger.info("fromage is set to run on cuda")

    logger.info("fromage is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_responses(image_path, prompt):
    logger.info(f"prompt generate responses {prompt}")
    ret_scale_factor = 0
    inp_image = utils.get_image_from_url(image_path)
    input_prompts = ["What is the image?"]
    if prompt != "":
        input_prompts = prompt

    logger.info(f"input_prompts {input_prompts}")
    input_context = [inp_image]
    text = ""
    for p in input_prompts:
        text += "Q: " + p + "\nA:"
        model_prompt = input_context + [text]
        model_outputs = model.generate_for_images_and_texts(
            model_prompt, num_words=32, ret_scale_factor=ret_scale_factor, max_num_rets=0
        )
        text += " ".join([s for s in model_outputs if type(s) == str]) + "\n"
    return model_outputs


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    responses = []
    try:
        frmg_answers = []
        image_path = request.json.get("image_paths", [])
        sentence = request.json.get("text", [])
        logger.info(f"img path {image_path}")
        logger.info(f"sentence {sentence}")
        outputs = generate_responses(image_path, sentence)
        frmg_answers += outputs
        logging.info(f"frmg_answers here {frmg_answers}")

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        frmg_answers = [[""]] * len(sentence)

    responses += [frmg_answers[-1]]
    total_time = time.time() - st_time
    logger.info(f"fromage exec time: {total_time:.3f}s")
    return jsonify(responses)
