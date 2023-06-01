import json
import logging
import os
import time

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from peft import PeftModel, PeftConfig
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from common.prompts import META_GOALS_PROMPT
from common.universal_templates import GENERATIVE_ROBOT_TEMPLATE


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
LANGUAGE = os.getenv("LANGUAGE", "EN")
NAMING = {
    "EN": ["AI", "Human"],
    "RU": ["Чат-бот", "Человек"],
}

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

DEFAULT_CONFIGS = {
    "transformers-lm-bloomz7b": json.load(open("common/generative_configs/default_generative_config.json", "r")),
    "transformers-lm-gptj": json.load(open("common/generative_configs/default_generative_config.json", "r")),
    "transformers-lm-oasst12b": json.load(open("common/generative_configs/default_generative_config.json", "r")),
}


def generate_responses(context, model, tokenizer, prompt, continue_last_uttr=False):
    outputs = []
    dialog_context = ""
    if prompt:
        dialog_context += prompt + "\n"
    s = len(context) % 2
    context = [f"{NAMING[LANGUAGE][(s + uttr_id) % 2]}: {uttr}" for uttr_id, uttr in enumerate(context)]
    if continue_last_uttr:
        dialog_context += "\n".join(context)
    else:
        dialog_context += "\n".join(context) + f"\n{NAMING[LANGUAGE][0]}:"

    logger.info(f"context inside generate_responses seen as: {dialog_context}")
    data = tokenizer([dialog_context], return_tensors="pt")
    data = {k: v.to(model.device) for k, v in data.items() if k in ("input_ids", "attention_mask")}

    with torch.no_grad():
        chat_history_ids = model.generate(
            **data,
            generation_config=default_config,
        )
    if torch.cuda.is_available():
        chat_history_ids = chat_history_ids.cpu()
    for result in chat_history_ids:
        output = tokenizer.decode(result, skip_special_tokens=True)
        result_cut = output.replace(dialog_context + " ", "")
        result_cut = [x.strip() for x in GENERATIVE_ROBOT_TEMPLATE.split(result_cut) if x.strip()][0]
        logger.info(f"hypothesis: {result_cut}")
        outputs.append(result_cut)

    return outputs


try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)

    default_config = GenerationConfig.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)

    config = PeftConfig.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_name_or_path,
        torch_dtype=torch.float16,
        # load_in_8bit=True,
        # device_map="auto"
    )
    model = PeftModel.from_pretrained(model, PRETRAINED_MODEL_NAME_OR_PATH)
    model.eval()

    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("transformers_peft_lm is set to run on cuda")

    example_response = generate_responses(
        ["What is the goal of SpaceX?"], model, tokenizer, "You are a SpaceX Assistant.", default_config
    )
    logger.info(f"example response: {example_response}")
    logger.info("transformers_peft_lm is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    prompts = request.json.get("prompts", [])
    if len(contexts) > 0 and len(prompts) == 0:
        prompts = [""] * len(contexts)

    try:
        responses = []
        for context, prompt in zip(contexts, prompts):
            curr_responses = []
            outputs = generate_responses(context, model, tokenizer, prompt)
            for response in outputs:
                if len(response) >= 2:
                    curr_responses += [response]
                else:
                    curr_responses += [""]
            responses += [curr_responses]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)

    logger.info(f"transformers_peft_lm output: {responses}")
    total_time = time.time() - st_time
    logger.info(f"transformers_peft_lm exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/generate_goals", methods=["POST"])
def generate_goals():
    st_time = time.time()

    prompts = request.json.get("prompts", None)
    prompts = [] if prompts is None else prompts

    try:
        responses = []
        for prompt in prompts:
            context = ["hi", META_GOALS_PROMPT + f"\nPrompt: '''{prompt}'''\nResult:"]
            goals_for_prompt = generate_responses(context, model, tokenizer, "")[0]
            logger.info(f"Generated goals: `{goals_for_prompt}` for prompt: `{prompt}`")
            responses += [goals_for_prompt]

    except Exception as exc:
        logger.info(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(prompts)

    total_time = time.time() - st_time
    logger.info(f"openai-api generate_goals exec time: {total_time:.3f}s")
    return jsonify(responses)
