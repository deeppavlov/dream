import json
import logging
import yaml
import time
from os import getenv, listdir

import sentry_sdk
from flask import Flask, request, jsonify
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
PROMPT_FILE = getenv("PROMPT_FILE")
assert PROMPT_FILE, logger.error("No prompt provided")
with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
DEFAULT_SKILLS = ["dummy_skill"]
MAX_N_SKILLS = int(getenv("MAX_N_SKILLS"))
PROMPT = PROMPT.replace("up to MAX_N_SKILLS", f"up to {MAX_N_SKILLS}")

assert GENERATIVE_SERVICE_URL


def collect_descriptions_from_components(skill_names):
    result = {}
    for fname in listdir("components/"):
        if "yml" in fname:
            component = yaml.load(open(f"components/{fname}", "r"), Loader=yaml.FullLoader)
            if component["name"] in skill_names:
                result[component["name"]] = component["description"]

    return result


def select_skills(dialog):
    global PROMPT, N_UTTERANCES_CONTEXT
    selected_skills = []
    selected_skills += DEFAULT_SKILLS

    dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
    human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})
    pipeline = dialog.get("attributes", {}).get("pipeline", [])
    # pipeline is smth like this: ['annotators.sentseg', 'skills.dummy_skill',
    # 'candidate_annotators.sentence_ranker', 'response_selectors.response_selector', ...]
    all_skill_names = [el.split(".")[1] for el in pipeline if "skills" in el]

    try:
        if "LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS" in PROMPT:
            # need to add skill descriptions in prompt in replacement of `LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS`
            skill_descr_dict = collect_descriptions_from_components(all_skill_names)
            skill_descriptions = "Skills:\n"
            skill_descriptions += "\n".join([f'"{name}": "{descr}"' for name, descr in skill_descr_dict.items()])
            PROMPT = PROMPT.replace("LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS", skill_descriptions)

        logger.info(f"llm_based_skill_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"llm_based_skill_selector sends prompt to llm:\n`{PROMPT}`")

        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
        )
        response = send_request_to_prompted_generative_service(
            dialog_context,
            PROMPT,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        for skill_name in all_skill_names:
            if skill_name in response[0]:
                selected_skills += [skill_name]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        logger.info("Exception in LLM's invocation. Turn on all skills from pipeline.")

    logger.info(f"llm_based_skill_selector selected:\n`{selected_skills}`")

    selected_skills = list(set(selected_skills))
    if selected_skills == ["dummy_skill"]:
        logger.info("Selected only Dummy Skill. Turn on all skills from pipeline.")
        selected_skills.extend(all_skill_names)
    return selected_skills


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs = request.json.get("dialogs", [])
    responses = []

    for dialog in dialogs:
        responses.append(select_skills(dialog))

    total_time = time.time() - st_time
    logger.info(f"llm_based_skill_selector exec time = {total_time:.3f}s")

    return jsonify(responses)
