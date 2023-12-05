import re
import json
import logging
import sentry_sdk
import requests
import os
from typing import List, Tuple, Any
from common.text_processing_for_prompts import (
    check_token_number,
    split_transcript_into_chunks,
)
from common.containers import get_max_tokens_for_llm
from common.prompts import send_request_to_prompted_generative_service
from common.files_and_folders_processing import upload_document

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

INCLUDE_INTO_REPORT = ["progress_by_areas", "problems", "summary_short"]
SEP_FOR_DOC_RESPONSES = "\n****************\n"
LONG_SUMMARY_REQUEST = re.compile(r"(detailed)|(long)", flags=re.IGNORECASE)
SHORT_SUMMARY_REQUEST = re.compile(r"(short)|(concise)", flags=re.IGNORECASE)
FILENAME = re.compile(r"\*\*\*FILENAME: (.*)\*\*\*")
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
GENERATIVE_SERVICE_URL = os.getenv("GENERATIVE_SERVICE_URL")

management_prompts_dict = {
    "summary": {},
    "personal_future_tasks": {},
    "future_tasks": {},
    "personal_completed_tasks": {},
    "completed_tasks": {},
    "decisions": {},
    "question_answering": {},
    "progress_by_areas": {},
    "weekly_report": {},
    "problems": {},
    "combine_responses": {},
}

with open("common/prompts/management_assistant/formatting.json", "r") as f:
    formatting_dict = json.load(f)
    SHORT_RESPONSE_GUIDELINES = formatting_dict["instruction_short_response"]
    MEDIUM_RESPONSE_GUIDELINES = formatting_dict["instruction_medium_response"]
    LONG_RESPONSE_GUIDELINES = formatting_dict["instruction_long_response"]
    BASIC_FORMATTING_GUIDELINES = formatting_dict["instruction_to_format"]
    NON_FORMATTING_GUIDELINES = formatting_dict["instruction_not_to_format"]

with open("common/prompts/management_assistant/default_system_prompt_assistant.json", "r") as f:
    DEFAULT_SYSTEM_PROMPT = json.load(f)["prompt"]

for key in management_prompts_dict.keys():
    with open(f"common/prompts/management_assistant/{key}.json", "r") as f:
        prompt_dict = json.load(f)
        management_prompts_dict[key]["prompt"] = prompt_dict["prompt"]
        management_prompts_dict[key]["prompt_concatenate"] = prompt_dict["prompt_concatenate"]


def get_older_gen_response(item_type_and_id, bot_attrs_files):
    hypothesis_link = bot_attrs_files[item_type_and_id]
    old_response = requests.get(hypothesis_link, timeout=FILE_SERVER_TIMEOUT).text
    logger.info(f"Found and downloaded {item_type_and_id} generated earlier.")
    return old_response


def set_correct_type_and_id(request, prompt_type_local, document_in_use_id=""):
    # if we need a weekly report, on this step we gather separate daily reports for each doc
    prompt_type_and_id = ""
    if prompt_type_local == "weekly_report":
        if document_in_use_id:
            prompt_type_and_id = f"full_report__{document_in_use_id}"
    else:
        if prompt_type_local == "summary":
            is_long_request = LONG_SUMMARY_REQUEST.search(request)
            is_short_request = SHORT_SUMMARY_REQUEST.search(request)
            if is_long_request:
                prompt_type_local += "_long"
            elif is_short_request:
                prompt_type_local += "_short"
        if document_in_use_id:
            prompt_type_and_id = f"{prompt_type_local}__{document_in_use_id}"
    return prompt_type_local, prompt_type_and_id


def get_response_for_prompt_type(
    transcript_chunks: list,
    prompt_type: str,
    dialog_context: list,
    sending_variables: dict,
    username: str = None,
    format_the_response: bool = False,
) -> str:
    if "summary" in prompt_type:
        if "summary_short" in prompt_type:
            length_request = SHORT_RESPONSE_GUIDELINES
        elif "summary_long" in prompt_type:
            length_request = LONG_RESPONSE_GUIDELINES
        else:
            length_request = MEDIUM_RESPONSE_GUIDELINES
        prompt_type = "summary"
    else:
        length_request = ""
    all_gpt_responses = []
    # this is prompt for processing each separate chunk of text
    prompt = management_prompts_dict[prompt_type]["prompt"]
    # this is prompt for processing the results for all chunks to get the final response
    # only used if the document is longer than the model's context window - 1000
    prompt_final = management_prompts_dict[prompt_type]["prompt_concatenate"]
    if format_the_response:
        if len(transcript_chunks) == 1:
            prompt += f" {BASIC_FORMATTING_GUIDELINES}"
        else:
            prompt += f" {NON_FORMATTING_GUIDELINES}"
            prompt_final += f" {BASIC_FORMATTING_GUIDELINES}"
    else:
        prompt += f" {NON_FORMATTING_GUIDELINES}"
        prompt_final += f" {NON_FORMATTING_GUIDELINES}"
    if username:
        prompt = prompt.replace("{username}", username)
    else:
        prompt = prompt.replace("{username}", "User request")
    request = dialog_context[-1]
    for n, chunk in enumerate(transcript_chunks):
        prompt_to_send = prompt.replace("{transcript_chunk}", chunk)
        prompt_to_send += length_request
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
        prompt_final_to_send += length_request
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
    # we do not upload question_answering as questions may vary
    # we do not upload combine_responses because combine_responses type is only used for internal processing
    # the response generated in combine_responses will be uploaded later at its original name
    uploaded_doc_link = ""
    if "combine_responses" not in prompt_type_and_id and "question_answering" not in prompt_type_and_id:
        logger.info(f"Saving {prompt_type_and_id} to related_files.")
        filename = f"{prompt_type_and_id}.txt"
        uploaded_doc_link = upload_document(hypothesis, filename, FILE_SERVER_URL, FILE_SERVER_TIMEOUT, type_ref="text")
    return uploaded_doc_link


def compose_and_upload_final_response(
    hyps_and_names_all_docs: list,
    prompt_type_and_id: str,
    dialog_context: List[str],
    sending_variables: dict,
    bot_attrs_files: dict,
    use_filenames: True = bool,
    username: str = None,
) -> Tuple[List[str], dict]:
    # note that we are joining responses for all docs by a special character SEP_FOR_DOC_RESPONSES
    # when we are sending them to LLM, if we need to split the info into chunks, we
    # will do that by SEP_FOR_DOC_RESPONSES, not by newline
    if use_filenames:
        newline = "\n"
        info_to_provide_to_llm = [f"FILENAME: {hyps[0]}{newline}{hyps[1]}" for hyps in hyps_and_names_all_docs]
    else:
        info_to_provide_to_llm = [hyps[1] for hyps in hyps_and_names_all_docs]
    hyps_from_all_docs = SEP_FOR_DOC_RESPONSES.join(info_to_provide_to_llm)
    if "weekly_report" not in prompt_type_and_id:
        prompt_type_and_id_for_processing = f"combine_responses__{prompt_type_and_id.split('__')[1]}"
    else:
        prompt_type_and_id_for_processing = prompt_type_and_id
    hyp_combined, bot_attrs_files = get_and_upload_response_for_one_doc(
        hyps_from_all_docs,
        prompt_type_and_id_for_processing,
        dialog_context,
        sending_variables,
        bot_attrs_files,
        username,
    )
    uploaded_doc_link = upload_generated_item_return_link(hyp_combined, prompt_type_and_id)
    if uploaded_doc_link:
        bot_attrs_files[prompt_type_and_id] = uploaded_doc_link
    return [hyp_combined], bot_attrs_files


def get_and_upload_response_for_one_doc(
    orig_text: str,
    prompt_type_and_id: str,
    dialog_context: List[str],
    sending_variables: dict,
    bot_attrs_files: dict,
    username: str = None,
) -> Tuple[str, dict]:
    prompt_type = prompt_type_and_id.split("__")[0]
    document_in_use_id = prompt_type_and_id.split("__")[1]
    _format_the_response = False
    # hard-coded limit: we preserve 1000 tokens for LLM answer
    token_limit = get_max_tokens_for_llm(GENERATIVE_SERVICE_URL) - 1000

    # if we have multiple docs, we would like not to split one doc into two
    # so in this case we split by special separator
    if prompt_type == "weekly_report" or prompt_type == "combine_responses":
        transcript_chunks = split_transcript_into_chunks(orig_text, limit=token_limit, sep=SEP_FOR_DOC_RESPONSES)
        _format_the_response = True
    else:
        transcript_chunks = split_transcript_into_chunks(orig_text, limit=token_limit)

    # if asked for full report, we get parts of it separately and then just concatenate them
    if prompt_type == "full_report":
        hypothesis = ""

        for item in INCLUDE_INTO_REPORT:
            item_type_and_id = f"{item}__{document_in_use_id}"
            if item_type_and_id in bot_attrs_files.keys():
                part_of_report = get_older_gen_response(item_type_and_id, bot_attrs_files)
                hypothesis += f"{part_of_report}\n\n"
            else:
                logger.info(f"No earlier {item_type_and_id} for full_report found.")
                part_of_report = get_response_for_prompt_type(
                    transcript_chunks, item, dialog_context, sending_variables, username, format_the_response=True
                )
                uploaded_doc_link = upload_generated_item_return_link(part_of_report, item_type_and_id)
                if uploaded_doc_link:
                    bot_attrs_files[item_type_and_id] = uploaded_doc_link
                hypothesis += f"{part_of_report}\n\n"
        hypothesis = hypothesis.strip()
    else:
        hypothesis = get_response_for_prompt_type(
            transcript_chunks,
            prompt_type,
            dialog_context,
            sending_variables,
            username,
            format_the_response=_format_the_response,
        )

    # we save each hyp to server under the name of the request and doc_in_use id
    uploaded_doc_link = upload_generated_item_return_link(hypothesis, prompt_type_and_id)
    if uploaded_doc_link:
        bot_attrs_files[prompt_type_and_id] = uploaded_doc_link
    return hypothesis, bot_attrs_files


def get_name_and_text_from_file(transcript_link: str) -> Tuple[str, str]:
    orig_file = requests.get(transcript_link, timeout=FILE_SERVER_TIMEOUT)
    orig_text = orig_file.text
    filename = FILENAME.search(orig_text).group(1)
    return filename, orig_text


def get_key_by_value(dictionary: dict, value_to_find: Any) -> str:
    for key, value in dictionary.items():
        if value == value_to_find:
            return key
    return ""
