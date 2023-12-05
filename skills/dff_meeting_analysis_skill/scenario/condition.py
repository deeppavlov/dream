import json
import logging
import requests
import os
import time
import re

import common.dff.integration.context as int_ctx

from df_engine.core import Actor, Context
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import (
    send_request_to_prompted_generative_service,
    compose_sending_variables,
)
from common.utils import no_templates

logger = logging.getLogger(__name__)
# ....

SHORT_GENERATIVE_SERVICE_URL = os.getenv("SHORT_GENERATIVE_SERVICE_URL")
assert SHORT_GENERATIVE_SERVICE_URL, logger.error("Error: SHORT_GENERATIVE_SERVICE_URL is not specified in env")

while True:
    result = is_container_running(SHORT_GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"SHORT_GENERATIVE_SERVICE_URL: {SHORT_GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

SHORT_GENERATIVE_SERVICE_CONFIG = os.getenv("SHORT_GENERATIVE_SERVICE_CONFIG")
if SHORT_GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{SHORT_GENERATIVE_SERVICE_CONFIG}", "r") as f:
        SHORT_GENERATIVE_SERVICE_CONFIG = json.load(f)

with open("common/prompts/management_assistant/default_system_prompt_checker.json", "r") as f:
    DEFAULT_SYSTEM_PROMPT = json.load(f)["prompt"]

with open("common/prompts/management_assistant/relevance_check.json", "r") as f:
    CHECK_RELEVANCE_PROMPT = json.load(f)["prompt"]

SHORT_GENERATIVE_TIMEOUT = float(os.getenv("SHORT_GENERATIVE_TIMEOUT", 30))
SHORT_GENERATIVE_TIMEOUT = (
    SHORT_GENERATIVE_SERVICE_CONFIG.pop("timeout", SHORT_GENERATIVE_TIMEOUT)
    if SHORT_GENERATIVE_SERVICE_CONFIG
    else SHORT_GENERATIVE_TIMEOUT
)

N_UTTERANCES_CONTEXT = int(os.getenv("N_UTTERANCES_CONTEXT"))
FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")
FILE_SERVER_TIMEOUT = float(os.getenv("FILE_SERVER_TIMEOUT"))
SHORT_ENVVARS_TO_SEND = get_envvars_for_llm(SHORT_GENERATIVE_SERVICE_URL)


def is_a_list():
    def is_a_list_handler(ctx: Context, actor: Actor) -> bool:
        _is_a_list = False
        last_human_uttr = int_ctx.get_last_human_utterance(ctx, actor)["text"]
        if re.match(r"- ", last_human_uttr) or len(re.split(r"\n ?- ?", last_human_uttr)) > 1:
            _is_a_list = True
        return _is_a_list

    return is_a_list_handler


def no_document_in_use():
    def no_document_in_use_handler(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            document_in_use = []
        else:
            document_in_use = (
                ctx.misc["agent"]["dialog"]["human_utterances"][-1]
                .get("user", {})
                .get("attributes", {})
                .get("documents_in_use", {})
            )
        return not bool(document_in_use)

    return no_document_in_use_handler


def go_to_question_answering():  # if no summary then True
    def go_to_question_answering_handler(ctx: Context, actor: Actor) -> bool:
        go_to_qa_node = True
        if not ctx.validation:
            summaries = []
            dialog = int_ctx.get_dialog(ctx, actor)
            bot_utts = dialog.get("bot_utterances", [{}])
            documents_in_use = (
                dialog.get("human_utterances", [{}])[-1]
                .get("user", {})
                .get("attributes", {})
                .get("documents_in_use", [])
            )
            if bot_utts:
                for doc in documents_in_use:
                    summary_link = (
                        bot_utts[-1]
                        .get("user", {})
                        .get("attributes", {})
                        .get("related_files", {})
                        .get(f"summary__{doc}", None)
                    )
                    if summary_link:
                        try:
                            summary = requests.get(summary_link, timeout=FILE_SERVER_TIMEOUT).text
                            summaries.append(summary)
                        except Exception:
                            pass
            # if we have summary for each doc in use,
            # check if the user request is relevant to any of them
            if summaries and documents_in_use and len(summaries) == len(documents_in_use):
                logger.info(
                    "Check if current document summaries are relevant \
                            to user request before entering question_answering node."
                )
                human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
                dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
                sending_variables = compose_sending_variables({}, SHORT_ENVVARS_TO_SEND, human_uttr_attributes)
                request = dialog_context[-1]
                summaries_concat = "\n\n".join(summaries)
                dialog_context[-1] = CHECK_RELEVANCE_PROMPT.replace("{request}", request).replace(
                    "{summary}", summaries_concat
                )
                response = send_request_to_prompted_generative_service(
                    dialog_context,
                    DEFAULT_SYSTEM_PROMPT,
                    SHORT_GENERATIVE_SERVICE_URL,
                    SHORT_GENERATIVE_SERVICE_CONFIG,
                    SHORT_GENERATIVE_TIMEOUT,
                    sending_variables,
                )
                response = response[0]
                if re.search(no_templates, response.lower()):
                    go_to_qa_node = False
                    logger.info("User request is NOT relevant to the current document.")
                else:
                    logger.info("User request is relevant to the current document.")
        return go_to_qa_node

    return go_to_question_answering_handler
