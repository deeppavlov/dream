import json
import logging
import time
import copy
from os import getenv
from typing import List

import sentry_sdk
from flask import Flask, request, jsonify
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.selectors import collect_descriptions_from_components


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
N_TURNS_TO_KEEP_DOC = getenv("N_TURNS_TO_KEEP_DOC")
if N_TURNS_TO_KEEP_DOC:
    N_TURNS_TO_KEEP_DOC = int(N_TURNS_TO_KEEP_DOC)
PROMPT_FILE = getenv("PROMPT_FILE")
assert PROMPT_FILE, logger.error("No prompt provided")
with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]

ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
DEFAULT_SKILLS = ["dummy_skill"]

assert GENERATIVE_SERVICE_URL


def turn_on_skills_for_documents(
    all_skill_names: List[str],
    selected_skills: List[str],
    prev_used_docs: List[str],
    prev_active_skills: List[str],
) -> List[str]:
    # if we have doc in use now, we always add dff_document_qa_llm_skill to selected skills
    if "dff_document_qa_llm_skill" in all_skill_names:
        logger.info("Document in use found. Turn on dff_document_qa_llm_skill.")
        selected_skills.append("dff_document_qa_llm_skill")
    # if we have N_TURNS_TO_KEEP_DOC, we can also check if we used dff_meeting_analysis_skill
    # with the same doc recently and if yes, append it to selected skills automatically
    if N_TURNS_TO_KEEP_DOC and prev_used_docs and prev_active_skills:
        last_n_used_docs = prev_used_docs[-N_TURNS_TO_KEEP_DOC:]
        # count in how many of steps was the active doc present
        n_steps_with_same_doc = num_of_steps_with_same_doc(last_n_used_docs)
        # get all skills that were active when the same doc was present
        last_n_active_skills_with_same_doc = prev_active_skills[-n_steps_with_same_doc:]
        # if we have doc in use and dff_meeting_analysis_skill was used earlier with the same doc,
        # we add dff_meeting_analysis_skill
        if (
            "dff_meeting_analysis_skill" in all_skill_names
            and "dff_meeting_analysis_skill" in last_n_active_skills_with_same_doc
        ):
            logger.info(
                "Document in use found and dff_meeting_analysis_skill was used for this doc earlier. \
Turn on dff_meeting_analysis_skill."
            )
            selected_skills.append("dff_meeting_analysis_skill")
    return selected_skills


def num_of_steps_with_same_doc(last_n_used_docs: List[str]) -> int:
    count = 0
    doc_in_use = last_n_used_docs[-1]
    for doc_to_check in list(reversed(last_n_used_docs))[1:]:
        if doc_to_check == doc_in_use:
            count += 1
        else:
            break
    return count


def select_skills(dialog: dict, all_prev_active_skills: List[str], all_prev_used_docs: List[str]) -> List[str]:
    global PROMPT, N_UTTERANCES_CONTEXT
    selected_skills = []
    selected_skills += DEFAULT_SKILLS

    dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
    dialog_context[-1] = f"{dialog_context[-1]}\nSelected skills/agents for this dialog context:"
    human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})
    pipeline = dialog.get("attributes", {}).get("pipeline", [])
    # pipeline is smth like this: ['annotators.sentseg', 'skills.dummy_skill',
    # 'candidate_annotators.sentence_ranker', 'response_selectors.response_selector', ...]
    all_skill_names = [el.split(".")[1] for el in pipeline if "skills" in el]
    # never changing all_skill_names, only changing all_available_skill_names
    all_available_skill_names = copy.deepcopy(all_skill_names)
    docs_in_use_info = dialog.get("human", {}).get("attributes", {}).get("documents_in_use", {})
    # no matter if we have doc in use now, remove dff_document_qa_llm_skill from skills to be sent to LLM
    # in any case, this skill will be added later
    # NB: meeting analysis skill is not removed and can be chosen even if there is no doc
    all_available_skill_names = [skill for skill in all_available_skill_names if skill != "dff_document_qa_llm_skill"]
    if human_uttr_attributes.get("selected_skills", None) in ["all", []]:
        logger.info(f"llm_based_skill_selector selected ALL skills:\n`{all_available_skill_names}`")
        return all_available_skill_names

    try:
        skills = [{"name": skill} for skill in all_available_skill_names]
        skill_descriptions_list, display_names_mapping = collect_descriptions_from_components(skills)
        if "LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS" in PROMPT:
            # need to add skill descriptions in prompt in replacement of `LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS`
            skill_descriptions = "Skills:\n"
            skill_descriptions += "\n".join([f'"{name}": "{descr}"' for name, descr in skill_descriptions_list])
            prompt_to_send = PROMPT.replace("LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS", skill_descriptions)

        logger.info(f"llm_based_skill_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"llm_based_skill_selector sends prompt to llm:\n`{prompt_to_send}`")

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
            prompt_to_send,
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

    if docs_in_use_info:
        selected_skills = turn_on_skills_for_documents(
            all_skill_names, selected_skills, all_prev_used_docs, all_prev_active_skills
        )
    selected_skills = list(set(selected_skills))
    logger.info(f"llm_based_skill_selector selected:\n`{selected_skills}`")

    if selected_skills == ["dummy_skill"]:
        logger.info("Selected only Dummy Skill. Turn on all skills from pipeline.")
        pipeline = dialog.get("attributes", {}).get("pipeline", [])
        selected_skills = list(set(selected_skills))
        selected_skills.extend(all_skill_names)
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
