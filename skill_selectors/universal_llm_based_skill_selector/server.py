import json
import logging
import time
import re
from os import getenv
from typing import List

import sentry_sdk
from flask import Flask, request, jsonify
from common.doc_based_skills_for_skills_selector import turn_on_doc_based_skills
from common.containers import get_envvars_for_llm
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

DEFAULT_LM_SERVICE_TIMEOUT = float(getenv("DEFAULT_LM_SERVICE_TIMEOUT", 5))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))

DEFAULT_PROMPT = json.load(open("common/prompts/skill_selector.json", "r"))["prompt"]
DEFAULT_LM_SERVICE_URL = getenv("DEFAULT_LM_SERVICE_URL", "http://transformers-lm-gptjt:8161/respond")
DEFAULT_LM_SERVICE_CONFIG = getenv("DEFAULT_LM_SERVICE_CONFIG", "default_generative_config.json")
DEFAULT_LM_SERVICE_CONFIG = json.load(open(f"common/generative_configs/{DEFAULT_LM_SERVICE_CONFIG}", "r"))
AVAILABLE_COMMANDS, COMMANDS_TO_SKILLS = None, None
ALL_SKILLS_DESCRIPTIONS_MAPPING = collect_descriptions_from_components_folder()


def select_skills(dialog: dict, prev_active_skills: List[str], prev_used_docs: List[str]) -> List[str]:
    global DEFAULT_PROMPT, N_UTTERANCES_CONTEXT, AVAILABLE_COMMANDS, COMMANDS_TO_SKILLS
    selected_skills = []
    selected_skills += DEFAULT_SKILLS

    dialog_context = [uttr["text"] for uttr in dialog["utterances"]]
    last_human_uttr = dialog_context[-1]
    dialog_context[-1] = f"{dialog_context[-1]}\nSelected skills/agents for this dialog context:"
    human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})

    all_skill_names = get_all_skill_names(dialog)
    _skill_selector = human_uttr_attributes.get("skill_selector", {})
    _is_prompt_based_selection = "prompt" in _skill_selector

    # on first iteration, get ALL commands from commands/ folder
    if not AVAILABLE_COMMANDS:
        COMMANDS_TO_SKILLS = get_available_commands_mapped_to_skills("all")
        if COMMANDS_TO_SKILLS:
            available_commands = [f".?({command}).?$" for command in list(COMMANDS_TO_SKILLS.keys())]
            AVAILABLE_COMMANDS = re.compile("|".join(available_commands), flags=re.IGNORECASE)

    # automatically turn on corresponding skill if user uttr contains a known command
    # however note that for universal skill selector all commands are known commands
    # thus we have to check later if skill associated with command is available
    if AVAILABLE_COMMANDS:
        commands_in_utt = AVAILABLE_COMMANDS.match(last_human_uttr)
        if commands_in_utt:
            discovered_command_groups = commands_in_utt.groups()
            discovered_command = next(command for command in discovered_command_groups if command)
            skills_to_select = COMMANDS_TO_SKILLS[discovered_command]
            # check if the skill is available
            for skill_to_select in skills_to_select:
                if skill_to_select in all_skill_names:
                    selected_skills.append(skill_to_select)
            if selected_skills:
                logger.info(
                    f"Command {discovered_command} detected in human utterance. \
Selected corresponding skill(s):`{selected_skills}`"
                )
            return selected_skills

    # if debugging response selector (selected_skills=all and skill_selector_prompt is not given):
    #   return all skills from pipeline conf
    # if debugging skill selector (skill_selector_prompt is given):
    #   -> ask LLM with prompt and skills descriptions for skills from human utterance attributes
    #   -> add skills from pipeline conf
    # the universal skill must generate only from the intersection of selected by Skill selector and given in attrs

    if human_uttr_attributes.get("selected_skills", None) in ["all", []] and not _is_prompt_based_selection:
        # MODE: debugging response selector
        # TURN ON: all skills from pipeline
        all_skill_names += ["dff_universal_prompted_skill"] + DEFAULT_SKILLS
        logger.info(f"universal_llm_based_skill_selector selected ALL skills:\n`{all_skill_names}`")
        return all_skill_names

    # no matter if we have doc in use now, remove dff_document_qa_llm_skill from skills to be sent to LLM
    # in any case, this skill will be added later
    # NB: meeting analysis skill is not removed and can be chosen even if there is no doc
    all_available_skill_names = [skill for skill in all_skill_names if skill != "dff_document_qa_llm_skill"]

    # MODE: debugging skill selector
    # TURN ON: all skills & turn on skills selected by LLM via prompt
    try:
        skills = [skill for skill in human_uttr_attributes["skills"] if skill["name"] in all_available_skill_names]
        current_skills_descs_mapping = update_descriptions_from_given_dict(ALL_SKILLS_DESCRIPTIONS_MAPPING, skills)
        prompt = _skill_selector.get("prompt", DEFAULT_PROMPT)
        if "LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS" in prompt:
            # need to add skill descriptions in prompt in replacement of `LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS`
            skill_descriptions = "Skills:\n"
            skill_descriptions += "\n".join(
                [
                    '"' + name_desc_dict["display_name"] + ": " + name_desc_dict["description"] + '"'
                    for name_desc_dict in current_skills_descs_mapping.values()
                ]
            )
            prompt = prompt.replace("LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS", skill_descriptions)

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
        lm_service_timeout = (
            lm_service_config.pop("timeout", DEFAULT_LM_SERVICE_TIMEOUT)
            if lm_service_config
            else DEFAULT_LM_SERVICE_TIMEOUT
        )
        n_utterances_context = (
            lm_service_config.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
            if lm_service_config
            else N_UTTERANCES_CONTEXT
        )

        logger.debug(f"universal_llm_based_skill_selector dialog context:\n`{dialog_context[-n_utterances_context:]}`")
        logger.debug(f"universal_llm_based_skill_selector prompt:\n`{prompt}`")

        response = send_request_to_prompted_generative_service(
            dialog_context[-n_utterances_context:],
            prompt,
            lm_service_url,
            lm_service_config,
            lm_service_timeout,
            sending_variables,
        )
        response = response[0]
        logger.info(f"universal_llm_based_skill_selector received from llm:\n`{response}`")
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
    # so, now we have selected_skills containing skills from human utterance attributes skill names (not deployed)
    # we need to add dff_universal_skill to generate prompt-based hypotheses
    selected_skills += ["dff_universal_prompted_skill"]
    # turn on skills active on the previous step and which have not CAN_NOT_CONTINUE tag
    selected_skills.extend(get_previously_active_skill(dialog))

    selected_skills = list(set(selected_skills))
    logger.info(f"universal_llm_based_skill_selector selected:\n`{selected_skills}`")
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
    logger.info(f"universal_llm_based_skill_selector exec time = {total_time:.3f}s")

    return jsonify(responses)
