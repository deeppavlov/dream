import json
import logging
import sentry_sdk
import os
from typing import Any
import time

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
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

DEFAULT_CONFIDENCE = 0.9
SUPER_CONFIDENCE = 1.0
LOW_CONFIDENCE = 0.7


def analyze_transcript(prompt_type: str):
    """
    prompt_type:  "summary", "future_tasks", "completed_tasks",
        "decisions", "question_answering", "progress_by_areas",
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

        prompt_type_local = prompt_type
        dialog = int_ctx.get_dialog(ctx, actor)
        context = dialog.get("utterances", [])[-N_UTTERANCES_CONTEXT:]
        related_files = {}
        n_requests = 0
        if context:
            dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
            request = dialog_context[-1]
            bot_utts = dialog.get("bot_utterances", [{}])
            human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
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
                _all_docs_have_summary = True
                _need_to_get_response_from_llm = True
                # check if have final hypothesis for this request in case of multiple docs in use
                if len(documents_in_use) > 1:
                    prompt_type_local, _ = set_correct_type_and_id(request, prompt_type_local)
                    curr_combination_id = get_key_by_value(docs_combination_ids, documents_in_use)
                    prompt_type_and_combination_id = f"{prompt_type_local}__{curr_combination_id}"
                    if prompt_type_and_combination_id in related_files.keys():
                        _need_to_get_response_from_llm = False
                        hypotheses = [get_older_gen_response(prompt_type_and_combination_id, related_files)]
                # check if have final hypothesis for this request in case of one doc in use
                else:
                    prompt_type_local, prompt_type_and_id = set_correct_type_and_id(
                        request, prompt_type_local, document_in_use_id=documents_in_use[0]
                    )
                    if prompt_type_and_id in related_files.keys():
                        _need_to_get_response_from_llm = False
                        hypotheses = [get_older_gen_response(prompt_type_and_id, related_files)]

                if _need_to_get_response_from_llm:
                    for document_in_use_id in documents_in_use:
                        if related_files.get(f"summary__{document_in_use_id}", None) is None:
                            _all_docs_have_summary = False
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
                                    hyp_one_doc, related_files, _n_requests = get_and_upload_response_for_one_doc(
                                        orig_text,
                                        prompt_type_and_id,
                                        dialog_context,
                                        sending_variables,
                                        related_files,
                                    )
                                    hyp_and_name_one_doc = [(filename, hyp_one_doc)]
                                    n_requests += _n_requests
                                except Exception as e:
                                    sentry_sdk.capture_exception(e)
                                    logger.exception(e)
                                    hyp_and_name_one_doc = []
                        else:
                            hyp_and_name_one_doc = []
                        hyps_and_names_all_docs += hyp_and_name_one_doc

                    if prompt_type == "question_answering" and _all_docs_have_summary:
                        # if we are in `question_answering` node then
                        # the condition `go_to_question_answering` was requested once
                        n_requests += 1
                    # having got responses for all docs, let's make one response from it
                    # just return the response if we have one document and one response
                    if len(hyps_and_names_all_docs) == 1 and prompt_type_local != "weekly_report":
                        hypotheses = [hyps_and_names_all_docs[0][1]]
                    else:
                        # earlier we set prompt_type_and_id for weekly_analysis to full report for each doc,
                        # now we need it to set it back
                        curr_combination_id = get_key_by_value(docs_combination_ids, documents_in_use)
                        prompt_type_and_id = f"{prompt_type_local}__{curr_combination_id}"
                        try:
                            # now by default we are passing filenames to LLM together with hypothesis for each file
                            # you can choose to pass only hypotheses (no filenames) by setting use_filenames=False
                            # when calling compose_and_upload_final_response()
                            hypotheses, related_files, _n_requests = compose_and_upload_final_response(
                                hyps_and_names_all_docs,
                                prompt_type_and_id,
                                dialog_context,
                                sending_variables,
                                related_files,
                            )
                            n_requests += _n_requests
                        except Exception as e:
                            sentry_sdk.capture_exception(e)
                            logger.exception(e)
                            hypotheses = []

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
            if len(hyp) and hyp[-1] not in [".", "?", "!"]:
                hyp += "."
                confidence = LOW_CONFIDENCE
            _curr_attrs = {
                "can_continue": CAN_NOT_CONTINUE,
                "llm_requests": {"llm_url": GENERATIVE_SERVICE_URL, "n_requests": n_requests},
            }
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
