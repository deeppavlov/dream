"""
Source code is https://github.com/Grossmend/DialoGPT/blob/master/src/service/service.py
"""
import logging
import time
import os
from typing import Dict, List

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get(
    "PRETRAINED_MODEL_NAME_OR_PATH", "Grossmend/rudialogpt3_medium_based_on_gpt2"
)
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)
    device = "cuda"
else:
    device = "cpu"

logger.info(f"dialogpt is set to run on {device}")

params_default = {
    "max_length": 256,
    "no_repeat_ngram_size": 3,
    "do_sample": True,
    "top_k": 100,
    "top_p": 0.9,
    "temperature": 0.6,
    "num_return_sequences": 3,
    "device": device,
    "is_always_use_length": True,
    "length_generate": "1",
}


class RussianDialogGPT:
    def __init__(self, path_model: str):
        self.path_model = path_model
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        logger.info(f"dialogpt Loading model: {self.path_model} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.path_model)
        self.model = AutoModelForCausalLM.from_pretrained(self.path_model)

    def get_responses(self, inputs: List[Dict], params: Dict) -> List[str]:

        params_ = {
            "max_length": params.get("max_length", params_default["max_length"]),
            "no_repeat_ngram_size": params.get("no_repeat_ngram_size", params_default["no_repeat_ngram_size"]),
            "do_sample": params.get("do_sample", params_default["do_sample"]),
            "top_k": params.get("top_k", params_default["top_k"]),
            "top_p": params.get("top_p", params_default["top_p"]),
            "temperature": params.get("temperature", params_default["temperature"]),
            "num_return_sequences": params.get("num_return_sequences", params_default["num_return_sequences"]),
            "device": params.get("device", params_default["device"]),
            "is_always_use_length": params.get("is_always_use_length", params_default["is_always_use_length"]),
            "length_generate": params.get("length_generate", params_default["length_generate"]),
        }

        inputs_text = ""
        for input_ in inputs:
            if params_["is_always_use_length"]:
                length_rep = len(self.tokenizer.encode(input_["text"]))
                if length_rep <= 15:
                    length_param = "1"
                elif length_rep <= 50:
                    length_param = "2"
                elif length_rep <= 256:
                    length_param = "3"
                else:
                    length_param = "-"
            else:
                length_param = "-"
            inputs_text += f"|{input_['speaker']}|{length_param}|{input_['text']}"
        inputs_text += f"|1|{params_['length_generate']}|"

        inputs_token_ids = self.tokenizer.encode(inputs_text, return_tensors="pt")
        inputs_token_ids = inputs_token_ids.cuda() if cuda else inputs_token_ids

        try:
            outputs_token_ids = self.model.generate(
                inputs_token_ids,
                max_length=params_["max_length"],
                no_repeat_ngram_size=params_["no_repeat_ngram_size"],
                do_sample=params_["do_sample"],
                top_k=params_["top_k"],
                top_p=params_["top_p"],
                temperature=params_["temperature"],
                num_return_sequences=params_["num_return_sequences"],
                device=params_["device"],
                mask_token_id=self.tokenizer.mask_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                unk_token_id=self.tokenizer.unk_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        except Exception as e:
            logger.info(f"dialogpt Error generate: {str(e)}")
            return ""

        outputs = [self.tokenizer.decode(x, skip_special_tokens=True) for x in outputs_token_ids]
        outputs = [x.split("|")[-1] for x in outputs]
        # outputs contains list of strings of possible hypotheses
        return outputs


try:
    model = RussianDialogGPT(PRETRAINED_MODEL_NAME_OR_PATH)
    model.model.eval()
    if cuda:
        model.model.cuda()

    logger.info("dialogpt model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialog_contexts = request.json.get("dialog_contexts", [])
    num_return_sequences = request.json.get("num_return_sequences", 5)

    try:
        batch_generated_responses = []
        for context in dialog_contexts:
            # context is a list of dicts, each dict contains text and speaker label
            # context = [{"text": "utterance text", "speaker": "human"}, ...]
            inputs = [{"text": uttr["text"], "speaker": 1 if uttr["speaker"] == "bot" else 0} for uttr in context][-3:]
            logger.info(f"dialogpt inputs: {inputs}")
            hypotheses = model.get_responses(inputs, params={"num_return_sequences": num_return_sequences})
            logger.info(f"dialogpt hypotheses: {hypotheses}")
            batch_generated_responses.append(hypotheses)

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        batch_generated_responses = [[]] * len(dialog_contexts)

    total_time = time.time() - st_time
    logger.info(f"dialogpt exec time: {total_time:.3f}s")

    return jsonify({"generated_responses": batch_generated_responses})
