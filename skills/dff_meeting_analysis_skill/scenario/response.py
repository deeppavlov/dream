import json
from copy import deepcopy
import logging
import sentry_sdk
import os
from typing import Any
import time
import requests

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_PROMPT, CAN_CONTINUE_SCENARIO
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import compose_sending_variables
from df_engine.core import Context, Actor
from .utils import (
    get_and_upload_response_for_one_doc,
    set_correct_type_and_id,
    compose_and_upload_final_response,
    get_older_gen_response,
    get_name_and_text_from_file,
    get_key_by_value,
)


sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_SERVICE_URL = os.getenv("GENERATIVE_SERVICE_URL")
assert GENERATIVE_SERVICE_URL, logger.error("Error: GENERATIVE_SERVICE_URL is not specified in env")

while True:
    result = is_container_running(GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"GENERATIVE_SERVICE_URL: {GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

GENERATIVE_SERVICE_CONFIG = os.getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(os.getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)
N_UTTERANCES_CONTEXT = int(os.getenv("N_UTTERANCES_CONTEXT"))
FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")
FILE_SERVER_TIMEOUT = float(os.getenv("FILE_SERVER_TIMEOUT"))
ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
BEARER_TOKEN_MICROSOFT_API = os.getenv("BEARER_TOKEN_MICROSOFT_API")
TRANSCRIPTOR_SERVICE_URL = os.getenv("TRANSCRIPTOR_SERVICE_URL")

with open("common/prompts/management_assistant/templates_for_response.json", "r") as f:
    formatting_dict = json.load(f)
    CHECK_THE_TASK_LIST_BY_BOT = formatting_dict["check_the_task_list_by_bot"]
    CHECK_THE_TASK_LIST_BY_USER = formatting_dict["check_the_task_list_by_user"]

DEFAULT_CONFIDENCE = 0.9
SUPER_CONFIDENCE = 1.0
LOW_CONFIDENCE = 0.7


def analyze_transcript(prompt_type: str):
    """
    prompt_type: "summary", "summary_short", "summary_long",
        "set_personal_tasks_into_tracker", "personal_future_tasks", "future_tasks",
        "personal_completed_tasks", "completed_tasks", "decisions", "question_answering", "progress_by_areas",
        "full_report", "weekly_report"
    """

    def transcript_analysis_handler(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]

        if prompt_type == "set_personal_tasks_into_tracker":
            prompt_type_local = "personal_future_tasks"
        else:
            prompt_type_local = prompt_type

        dialog = int_ctx.get_dialog(ctx, actor)
        context = dialog.get("utterances", [])[-N_UTTERANCES_CONTEXT:]
        related_files = {}
        username = None
        hypotheses_init = []

        if context:
            dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
            request = dialog_context[-1]
            bot_utts = dialog.get("bot_utterances", [{}])
            human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
            external_uid = context[-1].get("user", {}).get("user_external_id", "")
            if external_uid and BEARER_TOKEN_MICROSOFT_API and TRANSCRIPTOR_SERVICE_URL:
                usernames_dict = requests.get(
                    f"{TRANSCRIPTOR_SERVICE_URL}/users", headers={"Authorization": BEARER_TOKEN_MICROSOFT_API}
                ).json()
                username = next((item["displayName"] for item in usernames_dict if item["id"] == external_uid), None)
            docs_in_attributes = human_uttr_attributes.get("documents", [])
            if bot_utts:
                related_files = bot_utts[-1].get("user", {}).get("attributes", {}).get("related_files", {})
            # check if we already received such request before and saved hyp for it to server
            documents_in_use = context[-1].get("user", {}).get("attributes", {}).get("documents_in_use", [])
            docs_combination_ids = (
                context[-1].get("user", {}).get("attributes", {}).get("documents_combination_ids", {})
            )
            all_docs_info = context[-1].get("user", {}).get("attributes", {}).get("processed_documents", {})
            sending_variables = compose_sending_variables({}, ENVVARS_TO_SEND, human_uttr_attributes)
            hyps_and_names_all_docs = []
            if documents_in_use:
                _need_to_get_response_from_llm = True
                # check if have final hypothesis for this request in case of multiple docs in use
                if len(documents_in_use) > 1:
                    prompt_type_local, _ = set_correct_type_and_id(request, prompt_type_local)
                    curr_combination_id = get_key_by_value(docs_combination_ids, documents_in_use)
                    prompt_type_and_combination_id = f"{prompt_type_local}__{curr_combination_id}"
                    if prompt_type_and_combination_id in related_files.keys():
                        _need_to_get_response_from_llm = False
                        hypotheses_init = [get_older_gen_response(prompt_type_and_combination_id, related_files)]
                # check if have final hypothesis for this request in case of one doc in use
                else:
                    prompt_type_local, prompt_type_and_id = set_correct_type_and_id(
                        request, prompt_type_local, document_in_use_id=documents_in_use[0]
                    )
                    if prompt_type_and_id in related_files.keys():
                        _need_to_get_response_from_llm = False
                        hypotheses_init = [get_older_gen_response(prompt_type_and_id, related_files)]

                if _need_to_get_response_from_llm:
                    for document_in_use_id in documents_in_use:
                        # if we need a weekly report, on this step we gather separate daily reports for each doc
                        # also here we change the type of summary prompt based on summary length request
                        prompt_type_local, prompt_type_and_id = set_correct_type_and_id(
                            request, prompt_type_local, document_in_use_id=document_in_use_id
                        )
                        # we do not do anything unless we have the link to our file(s) in use
                        transcript_link = all_docs_info[document_in_use_id].get("processed_text_link", "")
                        if transcript_link:
                            # here we check if we already generated sth for the same request and the same doc
                            if prompt_type_and_id in related_files.keys():
                                # in the future, it is better to store filenames in related_files
                                # to avoid extra requests to file server
                                filename, _ = get_name_and_text_from_file(transcript_link)
                                older_response = get_older_gen_response(prompt_type_and_id, related_files)
                                hyp_and_name_one_doc = [(filename, older_response)]
                            # if no, let's generate it
                            else:
                                logger.info(
                                    f"No earlier {prompt_type_and_id} found. \
Sending request to generative model."
                                )
                                try:
                                    filename, orig_text = get_name_and_text_from_file(transcript_link)
                                    hyp_one_doc, related_files = get_and_upload_response_for_one_doc(
                                        orig_text,
                                        prompt_type_and_id,
                                        dialog_context,
                                        sending_variables,
                                        related_files,
                                        username,
                                    )
                                    hyp_and_name_one_doc = [(filename, hyp_one_doc)]
                                except Exception as e:
                                    sentry_sdk.capture_exception(e)
                                    logger.exception(e)
                                    hyp_and_name_one_doc = []
                        else:
                            hyp_and_name_one_doc = []
                        hyps_and_names_all_docs += hyp_and_name_one_doc

                    # having got responses for all docs, let's make one response from it
                    # just return the response if we have one document and one response
                    if len(hyps_and_names_all_docs) == 1 and prompt_type_local != "weekly_report":
                        hypotheses_init = [hyps_and_names_all_docs[0][1]]
                    else:
                        # earlier we set prompt_type_and_id for weekly_analysis to full report for each doc,
                        # now we need it to set it back
                        curr_combination_id = get_key_by_value(docs_combination_ids, documents_in_use)
                        prompt_type_and_id = f"{prompt_type_local}__{curr_combination_id}"
                        try:
                            # now by default we are passing filenames to LLM together with hypothesis for each file
                            # you can choose to pass only hypotheses (no filenames) by setting use_filenames=False
                            # when calling compose_and_upload_final_response()
                            hypotheses_init, related_files = compose_and_upload_final_response(
                                hyps_and_names_all_docs,
                                prompt_type_and_id,
                                dialog_context,
                                sending_variables,
                                related_files,
                                username,
                            )
                        except Exception as e:
                            sentry_sdk.capture_exception(e)
                            logger.exception(e)
                            hypotheses_init = []

                if prompt_type == "set_personal_tasks_into_tracker":
                    hypotheses = [f"{hyp}\n\n{CHECK_THE_TASK_LIST_BY_BOT}" for hyp in hypotheses_init]
                else:
                    hypotheses = deepcopy(hypotheses_init)

            # if there are docs in human utt attributes, but no processed docs in use were found
            elif docs_in_attributes:
                hyp_excuse = """Sorry, I failed to process the file you provided. \
Please, make sure that you provide a valid .docx file with Teams meeting transcript and try again."""
                hypotheses = [hyp_excuse]
            else:
                hyp_request_for_doc = "Please, upload the transcript that you want to discuss."
                hypotheses = [hyp_request_for_doc]
        else:
            hypotheses = []
        logger.info(f"generated hypotheses: {hypotheses}")
        bot_attrs = {"related_files": related_files}

        for hyp in hypotheses:
            confidence = DEFAULT_CONFIDENCE
            if prompt_type == "set_personal_tasks_into_tracker":
                _curr_attrs = {
                    "tasks_waiting_for_approval": hypotheses_init,
                    "can_continue": CAN_CONTINUE_PROMPT,
                }
            else:
                _curr_attrs = {
                    "can_continue": CAN_NOT_CONTINUE,
                }
            if len(hyp) and hyp[-1] not in [".", "?", "!"]:
                hyp += "."
                confidence = LOW_CONFIDENCE
            gathering_responses(hyp, confidence, {}, bot_attrs, _curr_attrs)

        if len(curr_responses) == 0:
            return ""

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)

    return transcript_analysis_handler


def ask_for_approval_to_set_updated_tasks() -> str:
    def get_confirmation_to_set_tasks_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]

        personal_tasks_corrected_by_user = (
            ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1].get("text", "")
        )

        response = f"{personal_tasks_corrected_by_user}\n\n{CHECK_THE_TASK_LIST_BY_USER}"
        confidence = DEFAULT_CONFIDENCE
        _curr_attrs = {
            "can_continue": CAN_CONTINUE_SCENARIO,
            "tasks_waiting_for_approval": personal_tasks_corrected_by_user,
        }
        gathering_responses(response, confidence, {}, {}, _curr_attrs)

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)

    return get_confirmation_to_set_tasks_handler


def respond_to_user_approval() -> str:
    def respond_to_user_approval_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]

        hyp = "Great! Setting your tasks to the task tracker..."
        last_bot_utt = ctx.misc.get("agent", {}).get("dialog", {}).get("bot_utterances", [{}])[-1]
        approved_tasks = last_bot_utt.get("attributes", {}).get("tasks_waiting_for_approval", "")
        tasks_from_task_list = [task.replace("-", "").strip() for task in approved_tasks.split("\n")]
        browser_agent_task = {"task": "add tasks to tracker", "tasks_to_set": tasks_from_task_list}
        logger.info(f"Create the following task for browser agent: {browser_agent_task}.")
        confidence = DEFAULT_CONFIDENCE
        _curr_attrs = {
            "can_continue": CAN_CONTINUE_SCENARIO,
            "browser_agent_task": browser_agent_task,
        }
        gathering_responses(hyp, confidence, {}, {}, _curr_attrs)

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)

    return respond_to_user_approval_handler
