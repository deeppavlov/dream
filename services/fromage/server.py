import logging
import os
import time
from fromage import models
from fromage import utils
import torch
import sentry_sdk
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")
RET_SCALE_FACTOR = int(os.getenv("RET_SCALE_FACTOR"))
logger.info(f"{RET_SCALE_FACTOR} and RET_SCALE_FACTOR type {type(RET_SCALE_FACTOR)}")


try:
    model_dir = "/services/fromage/fromage_model"
    model = models.load_fromage(model_dir)

    if torch.cuda.is_available():
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
    inp_image = [utils.get_image_from_url(image_path)]
    if prompt == "":
        prompt = ["What is the image?"]

    logger.info(f"prompts {prompt}")
    text = ""
    for p in prompt:
        text += f"Q: {p}\nA:"
        model_prompt = inp_image + [text]
        model_outputs = model.generate_for_images_and_texts(
            model_prompt, num_words=32, ret_scale_factor=RET_SCALE_FACTOR, max_num_rets=0
        )
        text += " ".join([s for s in model_outputs if isinstance(s, str)]) + "\n"
    return model_outputs


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    image_paths = request.json.get("image_paths", [])
    sentences = request.json.get("sentences", [])

    logger.info(f"img path {image_paths}")
    logger.info(f"sentence {sentences}")

    try:
        frmg_answers = []
        for image_path, sentence in zip(image_paths, sentences):
            outputs = generate_responses(image_path, sentence)
            frmg_answers += outputs
        logging.info(f"frmg_answers here {frmg_answers}")

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        frmg_answers = [[""]] * len(sentence)

    total_time = time.time() - st_time
    logger.info(f"fromage exec time: {total_time:.3f}s")
    return jsonify(frmg_answers)
