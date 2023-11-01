import json
import logging
import sentry_sdk
import os
from typing import Any, List
import requests
import time

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.containers import get_envvars_for_llm, get_max_tokens_for_llm, is_container_running
from common.prompts import (
    send_request_to_prompted_generative_service,
    compose_sending_variables,
)
from common.text_processing_for_prompts import (
    check_token_number,
    decide_where_to_break,
    split_transcript_into_chunks,
)
from common.files_and_folders_processing import upload_document
from df_engine.core import Context, Actor


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

with open("common/prompts/management_assistant/default_system_prompt_assistant.json", "r") as f:
    DEFAULT_SYSTEM_PROMPT = json.load(f)["prompt"]

GENERATIVE_TIMEOUT = float(os.getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)
N_UTTERANCES_CONTEXT = int(os.getenv("N_UTTERANCES_CONTEXT"))
FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")
FILE_SERVER_TIMEOUT = float(os.getenv("FILE_SERVER_TIMEOUT"))
ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
INCLUDE_INTO_REPORT = ["progress_by_areas", "problems", "summary"]
SEP_FOR_DOC_RESPONSES = "\n****************\n"

DEFAULT_CONFIDENCE = 0.9
SUPER_CONFIDENCE = 1.0
LOW_CONFIDENCE = 0.7

management_prompts_dict = {
    "summary": {},
    "future_tasks": {},
    "completed_tasks": {},
    "decisions": {},
    "question_answering": {},
    "progress_by_areas": {},
    "weekly_report": {},
    "problems": {},
    "combine_responses": {},
}

for key in management_prompts_dict.keys():
    with open(f"common/prompts/management_assistant/{key}.json", "r") as f:
        prompt_dict = json.load(f)
        management_prompts_dict[key]["prompt"] = prompt_dict["prompt"]
        management_prompts_dict[key]["prompt_concatenate"] = prompt_dict["prompt_concatenate"]


def get_response_for_prompts(
    transcript_chunks: list, prompt_type: str, dialog_context: list, sending_variables: dict
) -> str:
    all_gpt_responses = []
    # this is prompt for processing each separate chunk of text
    prompt = management_prompts_dict[prompt_type]["prompt"]
    # this is prompt for processing the results for all chunks to get the final response
    # only used if the document is longer than the model's context window - 1000
    prompt_final = management_prompts_dict[prompt_type]["prompt_concatenate"]
    request = dialog_context[-1]
    for n, chunk in enumerate(transcript_chunks):
        prompt_to_send = prompt.replace("{transcript_chunk}", chunk)
        dialog_context[-1] = prompt_to_send.replace("{request}", request)
        response = send_request_to_prompted_generative_service(
            dialog_context,
            DEFAULT_SYSTEM_PROMPT,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        logger.info(f"Got response for chunk {n+1}, tokens in response: {check_token_number(response[0])}.")
        all_gpt_responses += response
    if len(all_gpt_responses) > 1:
        logger.info("Processing multiple LLM's responses to get the final answer.")
        gpt_responses = "\n".join(all_gpt_responses)
        prompt_final_to_send = prompt_final.replace("{gpt_responses}", gpt_responses)
        dialog_context[-1] = prompt_final_to_send.replace("{request}", request)
        final_response = send_request_to_prompted_generative_service(
            dialog_context,
            DEFAULT_SYSTEM_PROMPT,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        all_gpt_responses += final_response
    return all_gpt_responses[-1]


def upload_generated_item_return_link(hypothesis: str, prompt_type_and_id: str):
    filename = f"{prompt_type_and_id}.txt"
    uploaded_doc_link = upload_document(hypothesis, filename, FILE_SERVER_URL, FILE_SERVER_TIMEOUT, type_ref="text")
    return uploaded_doc_link


def compose_and_upload_final_response(
    hyps_all_docs: list,
    prompt_type_and_id: str,
    dialog_context: List[str],
    sending_variables: dict,
    bot_attrs_files: dict,
):
    # note that we are joining responses for all docs by a special character SEP_FOR_DOC_RESPONSES
    # when we are sending them to LLM, if we need to split the info into chunks, we
    # will do that by SEP_FOR_DOC_RESPONSES, not by newline
    info_from_all_docs = SEP_FOR_DOC_RESPONSES.join(hyps_all_docs)
    if "weekly_report" not in prompt_type_and_id:
        prompt_type_and_id = f"combine_responses__{prompt_type_and_id.split('__')[1]}"
    hyp_week, bot_attrs_files = get_and_upload_response_for_one_doc(
        info_from_all_docs, prompt_type_and_id, dialog_context, sending_variables, bot_attrs_files
    )
    return hyp_week, bot_attrs_files


def get_and_upload_response_for_one_doc(
    orig_text: str, prompt_type_and_id: str, dialog_context: List[str], sending_variables: dict, bot_attrs_files: dict
) -> str:
    prompt_type = prompt_type_and_id.split("__")[0]
    document_in_use_id = prompt_type_and_id.split("__")[1]
    # hard-coded limit: we preserve 1000 tokens for LLM answer
    token_limit = get_max_tokens_for_llm(GENERATIVE_SERVICE_URL) - 1000

    # if we have multiple docs, we would like not to split one doc into two
    # so in this case we split by special separator
    if prompt_type == "weekly_report" or prompt_type == "combine_responses":
        break_points = decide_where_to_break(orig_text, limit=token_limit, sep=SEP_FOR_DOC_RESPONSES)
    else:
        break_points = decide_where_to_break(orig_text, limit=token_limit)
    transcript_chunks = split_transcript_into_chunks(orig_text, break_points)

    # if asked for full report, we get parts of it separately and then just concatenate them
    if prompt_type == "full_report":
        hypothesis = ""
        for item in INCLUDE_INTO_REPORT:
            item_type_and_id = f"{item}__{document_in_use_id}"
            part_of_report = get_response_for_prompts(transcript_chunks, item, dialog_context, sending_variables)
            uploaded_doc_link = upload_generated_item_return_link(part_of_report, item_type_and_id)
            bot_attrs_files[item_type_and_id] = uploaded_doc_link
            hypothesis += f"{part_of_report}\n\n"
    else:
        hypothesis = get_response_for_prompts(transcript_chunks, prompt_type, dialog_context, sending_variables)

    # we save each hyp to server under the name of the request and doc_in_use id
    # except for question_answering and combine_responses which we don't save as questions may vary
    if prompt_type != "question_answering" and prompt_type != "combine_responses":
        uploaded_doc_link = upload_generated_item_return_link(hypothesis, prompt_type_and_id)
        bot_attrs_files[prompt_type_and_id] = uploaded_doc_link
    return [hypothesis], bot_attrs_files


def analyze_transcript(prompt_type: str):
    """
    prompt_type:  "summary", "future_tasks", "completed_tasks",
        "decisions", "question_answering", "progress_by_areas", "full_report"
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

        dialog = int_ctx.get_dialog(ctx, actor)
        context = dialog.get("utterances", [])[-N_UTTERANCES_CONTEXT:]
        bot_attrs_files = {}
        filepaths_on_server = []
        if context:
            dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
            bot_utts = dialog.get("bot_utterances", [{}])
            human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
            docs_in_attributes = human_uttr_attributes.get("documents", [])
            if bot_utts:
                bot_attrs_files = bot_utts[-1].get("user", {}).get("attributes", {}).get("related_files", {})
            # check if we already received such request before and saved hyp for it to server
            documents_in_use = context[-1].get("user", {}).get("attributes", {}).get("documents_in_use", [])
            all_docs_info = context[-1].get("user", {}).get("attributes", {}).get("processed_documents", {})
            hyps_all_docs = []
            if documents_in_use:
                for document_in_use_id in documents_in_use:
                    # if we need a weekly report, on this step we gather separate daily reports for each doc
                    if prompt_type == "weekly_report":
                        prompt_type_and_id = f"full_report__{document_in_use_id}"
                    else:
                        prompt_type_and_id = f"{prompt_type}__{document_in_use_id}"

                    # here we check if we already generated sth for the same request and the same doc
                    if prompt_type_and_id in bot_attrs_files.keys():
                        hypothesis_link = bot_attrs_files[prompt_type_and_id]
                        hyp_one_doc = [requests.get(hypothesis_link, timeout=FILE_SERVER_TIMEOUT).text]
                        logger.info(f"Found and downloaded {prompt_type_and_id} generated earlier.")
                    # if no, let's generate it
                    else:
                        logger.info(
                            f"""No earlier {prompt_type_and_id} found. Got transcript text from \
{filepaths_on_server}, now sending request to generative model."""
                        )
                        transcript_link = all_docs_info[document_in_use_id].get("processed_text_link", "")
                        sending_variables = compose_sending_variables({}, ENVVARS_TO_SEND, human_uttr_attributes)
                        if transcript_link:
                            try:
                                orig_file = requests.get(transcript_link, timeout=FILE_SERVER_TIMEOUT)
                                orig_text = orig_file.text
                                hyp_one_doc, bot_attrs_files = get_and_upload_response_for_one_doc(
                                    orig_text, prompt_type_and_id, dialog_context, sending_variables, bot_attrs_files
                                )
                            except Exception as e:
                                sentry_sdk.capture_exception(e)
                                logger.exception(e)
                                hyp_one_doc = []
                        else:
                            hyp_one_doc = []
                    hyps_all_docs += hyp_one_doc

                # having got responses for all docs, let's make one response from it

                # just return the response if we have one document and one response
                if len(hyps_all_docs) == 1:
                    hypotheses = hyps_all_docs
                else:
                    # earlier we set prompt_type_and_id for weekly_analysis to full report for each doc,
                    # now we need it to set it back
                    prompt_type_and_id = f"{prompt_type}__{document_in_use_id}"
                    hypotheses, bot_attrs_files = compose_and_upload_final_response(
                        hyps_all_docs, prompt_type_and_id, dialog_context, sending_variables, bot_attrs_files
                    )
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
        bot_attrs = {"related_files": bot_attrs_files}

        for hyp in hypotheses:
            confidence = DEFAULT_CONFIDENCE
            if len(hyp) and hyp[-1] not in [".", "?", "!"]:
                hyp += "."
                confidence = LOW_CONFIDENCE
            _curr_attrs = {"can_continue": CAN_NOT_CONTINUE}
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
