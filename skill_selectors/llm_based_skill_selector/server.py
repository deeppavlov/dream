import json
import logging
import time
from os import getenv
from typing import List
import re

import sentry_sdk
from flask import Flask, request, jsonify
from common.containers import get_envvars_for_llm, is_container_running
from common.doc_based_skills_for_skills_selector import turn_on_doc_based_skills
from common.link import get_previously_active_skill
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.selectors import update_descriptions_from_given_dict, collect_descriptions_from_components_folder
from common.skill_selector_utils_and_constants import (
    DEFAULT_SKILLS,
    get_available_commands_mapped_to_skills,
    get_all_skill_names,
)


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
while True:
    result = is_container_running(GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"GENERATIVE_SERVICE_URL: {GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)

N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
N_UTTERANCES_CONTEXT = (
    GENERATIVE_SERVICE_CONFIG.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
    if GENERATIVE_SERVICE_CONFIG
    else N_UTTERANCES_CONTEXT
)
PROMPT_FILE = getenv("PROMPT_FILE")
assert PROMPT_FILE, logger.error("No prompt provided")
with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]

ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
AVAILABLE_COMMANDS, COMMANDS_TO_SKILLS = None, None

assert GENERATIVE_SERVICE_URL
ALL_SKILLS_DESCRIPTIONS_MAPPING = collect_descriptions_from_components_folder()


def select_skills(dialog: dict, prev_active_skills: List[str], prev_used_docs: List[str]) -> List[str]:
    global PROMPT, N_UTTERANCES_CONTEXT, AVAILABLE_COMMANDS, COMMANDS_TO_SKILLS
    selected_skills = []
    selected_skills += DEFAULT_SKILLS

    dialog_context = [uttr["text"] for uttr in dialog["utterances"]]
    last_human_uttr = dialog_context[-1]
    dialog_context[-1] = f"{dialog_context[-1]}\nSelected skills/agents for this dialog context:"
    human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})

    all_skill_names = get_all_skill_names(dialog)
    if human_uttr_attributes.get("selected_skills", None) in ["all", []]:
        logger.info(f"llm_based_skill_selector selected ALL skills:\n`{all_skill_names}`")
        return all_skill_names

    # on first iteration, get available commands and command-skill mapping
    # based on available skills
    if not AVAILABLE_COMMANDS:
        COMMANDS_TO_SKILLS = get_available_commands_mapped_to_skills(all_skill_names)
        if COMMANDS_TO_SKILLS:
            available_commands = [f".?({command}).?$" for command in list(COMMANDS_TO_SKILLS.keys())]
            AVAILABLE_COMMANDS = re.compile("|".join(available_commands), flags=re.IGNORECASE)

    # automatically turn on corresponding skill if user uttr contains a known command
    if AVAILABLE_COMMANDS:
        commands_in_utt = AVAILABLE_COMMANDS.match(last_human_uttr)
        if commands_in_utt:
            discovered_command_groups = commands_in_utt.groups()
            discovered_command = next(command for command in discovered_command_groups if command)
            skills_to_select = COMMANDS_TO_SKILLS[discovered_command]
            selected_skills += skills_to_select
            logger.info(
                f"Command {discovered_command} detected in human utterance. \
Selected corresponding skill(s):`{skills_to_select}`"
            )
            return list(set(selected_skills))

    # no matter if we have doc in use now, remove dff_document_qa_llm_skill from skills to be sent to LLM
    # in any case, this skill will be added later
    # NB: meeting analysis skill is not removed and can be chosen even if there is no doc
    all_available_skill_names = [skill for skill in all_skill_names if skill != "dff_document_qa_llm_skill"]

    try:
        skills = [{"name": skill} for skill in all_available_skill_names]
        current_skills_descs_mapping = update_descriptions_from_given_dict(ALL_SKILLS_DESCRIPTIONS_MAPPING, skills)

        if "LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS" in PROMPT:
            # need to add skill descriptions in prompt in replacement of `LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS`
            skill_descriptions = "Skills:\n"
            skill_descriptions += "\n".join(
                [
                    '"' + name_desc_dict["display_name"] + '": "' + name_desc_dict["description"] + '"'
                    for name_desc_dict in current_skills_descs_mapping.values()
                ]
            )
            prompt = PROMPT.replace("LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS", skill_descriptions)
        else:
            prompt = PROMPT

        lm_service_kwargs = human_uttr_attributes.get("skill_selector", {}).get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            ENVVARS_TO_SEND,
            human_uttr_attributes,
        )
        logger.debug(f"llm_based_skill_selector dialog context:\n`{dialog_context[-N_UTTERANCES_CONTEXT:]}`")
        logger.debug(f"llm_based_skill_selector prompt:\n`{prompt}`")

        response = send_request_to_prompted_generative_service(
            dialog_context[-N_UTTERANCES_CONTEXT:],
            prompt,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        response = response[0]
        logger.info(f"llm_based_skill_selector received from llm:\n`{response}`")
        for skill_name, name_desc_dict in current_skills_descs_mapping.items():
            if name_desc_dict["display_name"] in response:
                selected_skills += [skill_name]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        logger.info("Exception in LLM's invocation. Turn on all skills from pipeline.")

    if selected_skills == DEFAULT_SKILLS:
        logger.info("Selected only Dummy Skill. Turn on all skills from pipeline.")
        selected_skills.extend(all_skill_names)

    # now we also turn on document-based skills based on specific conditions
    # all_skill_names (available skills) are taken from human utt attributes
    selected_skills = turn_on_doc_based_skills(
        dialog,
        all_skill_names,
        selected_skills,
        prev_used_docs,
        prev_active_skills,
        auto_turn_on_meeting_analysis_when_doc_in_use=False,
    )
    # turn on skills active on the previous step and which have not CAN_NOT_CONTINUE tag
    selected_skills.extend(get_previously_active_skill(dialog))

    selected_skills = list(set(selected_skills))
    logger.info(f"llm_based_skill_selector selected:\n`{selected_skills}`")
    return selected_skills


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs = request.json.get("dialogs", [])
    all_prev_active_skills = request.json.get("all_prev_active_skills")
    all_prev_active_skills = [None for _ in dialogs] if all_prev_active_skills is None else all_prev_active_skills
    all_prev_used_docs = request.json.get("all_prev_used_docs")
    all_prev_used_docs = [None for _ in dialogs] if all_prev_used_docs is None else all_prev_used_docs
    responses = []

    for dialog, prev_active_skills, prev_used_docs in zip(dialogs, all_prev_active_skills, all_prev_used_docs):
        responses.append(select_skills(dialog, prev_active_skills, prev_used_docs))

    total_time = time.time() - st_time
    logger.info(f"llm_based_skill_selector exec time = {total_time:.3f}s")

    return jsonify(responses)
