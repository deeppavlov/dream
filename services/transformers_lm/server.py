import json
import logging
import os
import re
import time
from copy import deepcopy

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import StoppingCriteria, StoppingCriteriaList

from common.prompts import META_GOALS_PROMPT
from common.universal_templates import GENERATIVE_ROBOT_TEMPLATE


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
HALF_PRECISION = os.environ.get("HALF_PRECISION", 0)
HALF_PRECISION = 0 if HALF_PRECISION is None else bool(int(HALF_PRECISION))
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
LANGUAGE = os.getenv("LANGUAGE", "EN")
HF_ACCESS_TOKEN = os.environ.get("HF_ACCESS_TOKEN", None)
NAMING = {
    "EN": ["AI", "Human"],
    "RU": ["Assistant", "Human"],
}
ADDITIONAL_EOS_TOKENS = os.environ.get("ADDITIONAL_EOS_TOKENS", None)  # for RuXGLM: "<|endoftext|>,Human:"
if ADDITIONAL_EOS_TOKENS:
    ADDITIONAL_EOS_TOKENS = ADDITIONAL_EOS_TOKENS.split(",")

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

DEFAULT_CONFIGS = {
    "EleutherAI/gpt-j-6B": json.load(open("common/generative_configs/default_generative_config.json", "r")),
    "OpenAssistant/pythia-12b-sft-v8-7k-steps": json.load(
        open("common/generative_configs/default_generative_config.json", "r")
    ),
    "togethercomputer/GPT-JT-6B-v1": json.load(open("common/generative_configs/default_generative_config.json", "r")),
    "lmsys/vicuna-13b-v1.3": json.load(open("common/generative_configs/default_generative_config.json", "r")),
    "dim/xglm-4.5B_ru_v10_epoch_6_step_41141": json.load(open("common/generative_configs/ruxglm_config.json", "r")),
    "ai-forever/ruGPT-3.5-13B": json.load(open("common/generative_configs/rugpt35_config.json", "r")),
}
MAX_TOKENS = {
    "EleutherAI/gpt-j-6B": 2048,
    "OpenAssistant/pythia-12b-sft-v8-7k-steps": 5120,
    "togethercomputer/GPT-JT-6B-v1": 2048,
    "lmsys/vicuna-13b-v1.3": 2048,
    "dim/xglm-4.5B_ru_v10_epoch_6_step_41141": 2048,
    "ai-forever/ruGPT-3.5-13B": 2048,
}


def add_replacement_tokens(text, replacement):
    for pair in replacement:
        text = re.sub(pair[0], f"{pair[1]} ", text)
    return text


def remove_replacement_tokens(text, replacement):
    for pair in replacement:
        text = re.sub(pair[1], pair[0], text)

    text = text.replace("\n ", "\n")
    return text


def cut_predictions_by_additional_eos(text):
    if ADDITIONAL_EOS_TOKENS:
        for token in ADDITIONAL_EOS_TOKENS:
            text = text.split(token)[0]
    return text


class StoppingCriteriaSub(StoppingCriteria):
    def __init__(self, stops, tokenizer, prompt, replacement):
        super().__init__()
        self.stops = stops
        self.tokenizer = tokenizer
        self.prompt = add_replacement_tokens(prompt, replacement)
        self.prompt = tokenizer.decode(tokenizer.encode(self.prompt))

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            generated_temp_ids = input_ids.tolist()[0]
            if stop in tokenizer.decode(generated_temp_ids)[len(self.prompt) :]:
                return True

        return False


def generate_responses(context, model, tokenizer, prompt, generation_params, continue_last_uttr=False):
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

    replacement = generation_params.pop("replacement", [])
    logger.info(f"replacement: {replacement}")
    logger.info(f"generation_params: {generation_params}")
    dialog_context = add_replacement_tokens(dialog_context, replacement)
    logger.info(f"context inside generate_responses seen as: {dialog_context}")
    bot_input_ids = tokenizer([dialog_context], return_tensors="pt").input_ids
    stopping_criteria = StoppingCriteriaList(
        [
            StoppingCriteriaSub(
                stops=ADDITIONAL_EOS_TOKENS,
                tokenizer=tokenizer,
                prompt=dialog_context,
                replacement=replacement,
            )
        ]
    )
    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        chat_history_ids = model.generate(
            bot_input_ids,
            pad_token_id=tokenizer.eos_token_id,
            stopping_criteria=stopping_criteria,
            **generation_params,
        )
    if torch.cuda.is_available():
        chat_history_ids = chat_history_ids.cpu()
    for result in chat_history_ids:
        skip_special_tokens = False if replacement else True
        output = tokenizer.decode(result, skip_special_tokens=skip_special_tokens)
        # preprocess dialog context to correctly remove it from output
        dialog_context = re.sub(r"  +", " ", dialog_context)
        dialog_context = dialog_context.replace("\n ", "\n")
        output = re.sub(r"  +", " ", output)
        output = output.replace("\n ", "\n")

        result_cut = output.replace(dialog_context + " ", "")
        result_cut = cut_predictions_by_additional_eos(result_cut)
        result_cut = remove_replacement_tokens(result_cut, replacement)
        result_cut = [x.strip() for x in GENERATIVE_ROBOT_TEMPLATE.split(result_cut) if x.strip()][0]
        logger.info(f"hypothesis: {result_cut}")
        outputs.append(result_cut)

    return outputs


try:
    additional_kwargs = {}
    if HF_ACCESS_TOKEN:
        additional_kwargs["use_auth_token"] = HF_ACCESS_TOKEN

    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH, **additional_kwargs)

    if HALF_PRECISION:
        additional_kwargs["torch_dtype"] = torch.float16
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH, **additional_kwargs)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("transformers_lm is set to run on cuda")

    example_response = generate_responses(
        ["What is the goal of SpaceX?"],
        model,
        tokenizer,
        "You are a SpaceX Assistant.",
        deepcopy(DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH]),
    )
    logger.info(f"example response: {example_response}")
    logger.info("transformers_lm is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/envvars_to_send", methods=["POST"])
def envvars_to_send():
    return jsonify([])


@app.route("/max_tokens", methods=["POST"])
def max_tokens():
    global PRETRAINED_MODEL_NAME_OR_PATH
    return jsonify(MAX_TOKENS[PRETRAINED_MODEL_NAME_OR_PATH])


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    prompts = request.json.get("prompts", [])
    configs = request.json.get("configs", None)
    configs = [None] * len(prompts) if configs is None else configs
    configs = [deepcopy(DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH]) if el is None else el for el in configs]
    if len(contexts) > 0 and len(prompts) == 0:
        prompts = [""] * len(contexts)

    try:
        responses = []
        for context, prompt, config in zip(contexts, prompts, configs):
            curr_responses = []
            outputs = generate_responses(context, model, tokenizer, prompt, config)
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

    logger.info(f"transformers_lm output: {responses}")
    total_time = time.time() - st_time
    logger.info(f"transformers_lm exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/generate_goals", methods=["POST"])
def generate_goals():
    st_time = time.time()

    prompts = request.json.get("prompts", None)
    prompts = [] if prompts is None else prompts
    configs = request.json.get("configs", None)
    configs = [None] * len(prompts) if configs is None else configs
    configs = [deepcopy(DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH]) if el is None else el for el in configs]

    try:
        responses = []
        for prompt, config in zip(prompts, configs):
            context = ["hi", META_GOALS_PROMPT + f"\nPrompt: '''{prompt}'''\nResult:"]
            goals_for_prompt = generate_responses(context, model, tokenizer, "", config)[0]
            logger.info(f"Generated goals: `{goals_for_prompt}` for prompt: `{prompt}`")
            responses += [goals_for_prompt]

    except Exception as exc:
        logger.info(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(prompts)

    total_time = time.time() - st_time
    logger.info(f"openai-api generate_goals exec time: {total_time:.3f}s")
    return jsonify(responses)
