import logging
import os
import time
from fromage import models
from fromage import utils
import torch
from flask import Flask, request, jsonify

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")
RET_SCALE_FACTOR = int(os.environ.get("RET_SCALE_FACTOR"))

try:
    model_dir = "/services/fromage/fromage_model"
    model = models.load_fromage(model_dir)
    if torch.cuda.is_available():
        logger.info("fromage is set to run on cuda")

    logger.info("fromage is ready")
except Exception as e:
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

def generate_responses(image_path, conversation):
    inp_image = [utils.get_image_from_url(image_path)]
    if not conversation:
        conversation = [{"role": "user", "content": "What is the image?"}]
    elif isinstance(conversation, str):
        prompt = [{"role": "user", "content": conversation}]
    assert conversation[-1]['role'] == 'user'

    conversation_text = '\n'.join(('Q: ' if utt['role']=='user' else 'A: ')+utt['content']
                                  for utt in conversation)
    model_prompt = inp_image + [conversation_text]
    model_outputs = model.generate_for_images_and_texts(
        model_prompt, num_words=32, ret_scale_factor=RET_SCALE_FACTOR, max_num_rets=0
    )
    answer_text = " ;; ".join([s for s in model_outputs if isinstance(s, str)]) + "\n"
    conversation.append({'role': 'system', 'content': answer_text})
    return answer_text


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    # template_request = {"image_paths": ['ip1', 'ip2'], "sentences": ['is it good?', 'is it a dog?'],
    # ...
    # "histories": [[{'role':'user','content':'whats there'},{'role':'assistant','content':'a dog'}], []]}
    
    image_paths = request.json.get("image_paths")
    sentences = request.json.get("sentences")
    histories = request.json.get("histories")
    frmg_answers = []
    for image_path, sentence, history in zip(image_paths, sentences, histories):
        if image_path:
            conversation = history + [{'role': 'user', 'content': sentence}]
            try:
                outputs = generate_responses(image_path, conversation)
                frmg_answers += outputs
            except Exception as exc:
                logger.exception(exc)
                frmg_answers += [[""]]
        else:
            frmg_answers += [[""]]

    total_time = time.time() - st_time
    logger.info(f"fromage results: {frmg_answers}")
    logger.info(f"fromage exec time: {total_time:.3f}s")
    return jsonify(frmg_answers)
