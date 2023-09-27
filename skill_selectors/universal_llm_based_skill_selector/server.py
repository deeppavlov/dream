import json
import logging
import yaml
import time
from os import getenv, listdir
from typing import List

import sentry_sdk
from flask import Flask, request, jsonify
from common.containers import get_envvars_for_llm
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT", 5))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))

DEFAULT_PROMPT = json.load(open("common/prompts/skill_selector.json", "r"))["prompt"]
DEFAULT_LM_SERVICE_URL = getenv("DEFAULT_LM_SERVICE_URL", "http://transformers-lm-gptjt:8161/respond")
DEFAULT_LM_SERVICE_CONFIG = getenv("DEFAULT_LM_SERVICE_CONFIG", "default_generative_config.json")
DEFAULT_LM_SERVICE_CONFIG = json.load(open(f"common/generative_configs/{DEFAULT_LM_SERVICE_CONFIG}", "r"))

DEFAULT_SKILLS = ["dummy_skill"]


def collect_descriptions_from_components(skills: List[dict]):
    result = []
    all_skills = [skill["name"] for skill in skills]
    collected_skills = []

    # collect display names and descriptions from the request
    for skill in skills:
        if skill.get("display_name", "") and skill.get("description", ""):
            result += [(skill["display_name"], skill["description"])]
            collected_skills += [skill["name"]]

    # collect display names and descriptions of skills which descriptions are not given in request
    # from the components folder
    for fname in listdir("components/"):
        if "yml" in fname:
            component = yaml.load(open(f"components/{fname}", "r"), Loader=yaml.FullLoader)
            if component["name"] in all_skills and component["name"] not in collected_skills:
                result += [(component["display_name"], component["description"])]
                collected_skills += [component["name"]]

    # for the rest of unfound skills, compose description by hands
    for skill in skills:
        if skill["name"] not in collected_skills:
            prompt = skill["prompt"]
            result += [(skill["name"], f"Agent with the following task:\n`{prompt}`")]
    return result


def select_skills(dialog):
    global DEFAULT_PROMPT, N_UTTERANCES_CONTEXT
    selected_skills = []
    selected_skills += DEFAULT_SKILLS

    dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
    human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})

    _skill_selector = human_uttr_attributes.get("skill_selector", {})
    _is_prompt_based_selection = "prompt" in _skill_selector
    # if debugging response selector (selected_skills=all and skill_selector_prompt is not given):
    #   return all skills from pipeline conf
    # if debugging skill selector (skill_selector_prompt is given):
    #   -> ask LLM with prompt and skills descriptions for skills from human utterance attributes
    #   -> add skills from pipeline conf
    # the universal skill must generate only from the intersection of selected by Skill selector and given in attrs

    if human_uttr_attributes.get("selected_skills", None) in ["all", []] and not _is_prompt_based_selection:
        # MODE: debugging response selector
        # TURN ON: all skills from pipeline
        pipeline = dialog.get("attributes", {}).get("pipeline", [])
        all_skill_names = [el.split(".")[1] for el in pipeline if "skills" in el]
        logger.info(f"universal_llm_based_skill_selector selected ALL skills:\n`{all_skill_names}`")
        return all_skill_names

    # MODE: debugging skill selector
    # TURN ON: all skills & turn on skills selected by LLM via prompt
    try:
        logger.info(f"universal_llm_based_skill_selector sends dialog context to llm:\n`{dialog_context}`")
        prompt = _skill_selector.get("prompt", DEFAULT_PROMPT)

        if "LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS" in prompt:
            # need to add skill descriptions in prompt in replacement of `LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS`
            skill_descriptions_list = collect_descriptions_from_components(human_uttr_attributes.get("skills", []))
            skill_descriptions = "Skills:\n"
            skill_descriptions += "\n".join([f'"{name}": "{descr}"' for name, descr in skill_descriptions_list])
            prompt = prompt.replace("LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS", skill_descriptions)
        logger.info(f"prompt: {prompt}")

        lm_service_url = _skill_selector.get("lm_service", {}).get("url", DEFAULT_LM_SERVICE_URL)
        logger.info(f"lm_service_url: {lm_service_url}")
        # this is a dictionary! not a file!
        lm_service_config = _skill_selector.get("lm_service", {}).get("config", None)
        lm_service_kwargs = _skill_selector.get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = get_envvars_for_llm(lm_service_url)
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            human_uttr_attributes,
        )

        response = send_request_to_prompted_generative_service(
            dialog_context,
            prompt,
            lm_service_url,
            lm_service_config,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        logger.info(f"universal_llm_based_skill_selector received from llm:\n`{response}`")
        for skill in human_uttr_attributes.get("skills", []):
            if skill.get("display_name", skill["name"]) in response[0]:
                selected_skills += [skill["name"]]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        logger.info("Exception in LLM's invocation. Turn on all skills from pipeline.")
    # so, now we have selected_skills containing skills from human utterance attributes skill names (not deployed)

    # we need to add dff_universal_skill to generate prompt-based hypotheses
    selected_skills += ["dff_universal_prompted_skill"]
    logger.info(f"universal_llm_based_skill_selector selected:\n`{selected_skills}`")

    selected_skills = list(set(selected_skills))
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
    logger.info(f"universal_llm_based_skill_selector exec time = {total_time:.3f}s")

    return jsonify(responses)
