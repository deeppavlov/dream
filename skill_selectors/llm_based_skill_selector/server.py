import json
import logging
import time
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
from common.containers import get_envvars_for_llm
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.selectors import collect_descriptions_from_components


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)

N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
PROMPT_FILE = getenv("PROMPT_FILE")
assert PROMPT_FILE, logger.error("No prompt provided")
with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]

ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
DEFAULT_SKILLS = ["dummy_skill"]

assert GENERATIVE_SERVICE_URL


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
    if human_uttr_attributes.get("selected_skills", None) in ["all", []]:
        logger.info(f"llm_based_skill_selector selected ALL skills:\n`{all_skill_names}`")
        return all_skill_names

    try:
        skills = [{"name": skill} for skill in all_skill_names]
        skill_descriptions_list, display_names_mapping = collect_descriptions_from_components(skills)
        if "LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS" in PROMPT:
            # need to add skill descriptions in prompt in replacement of `LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS`
            skill_descriptions = "Skills:\n"
            skill_descriptions += "\n".join([f'"{name}": "{descr}"' for name, descr in skill_descriptions_list])
            PROMPT = PROMPT.replace("LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS", skill_descriptions)

        logger.info(f"llm_based_skill_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"llm_based_skill_selector sends prompt to llm:\n`{PROMPT}`")

        lm_service_kwargs = human_uttr_attributes.get("skill_selector", {}).get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            human_uttr_attributes,
        )
        response = send_request_to_prompted_generative_service(
            dialog_context,
            PROMPT,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )[0]
        logger.info(f"llm_based_skill_selector received from llm:\n`{response}`")
        for skill_name, display_name in display_names_mapping.items():
            if display_name in response:
                selected_skills += [skill_name]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        logger.info("Exception in LLM's invocation. Turn on all skills from pipeline.")

    selected_skills = list(set(selected_skills))
    logger.info(f"llm_based_skill_selector selected:\n`{selected_skills}`")

    if selected_skills == ["dummy_skill"]:
        logger.info("Selected only Dummy Skill. Turn on all skills from pipeline.")
        pipeline = dialog.get("attributes", {}).get("pipeline", [])
        all_skill_names = [el.split(".")[1] for el in pipeline if "skills" in el]
        selected_skills = list(set(selected_skills))
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
