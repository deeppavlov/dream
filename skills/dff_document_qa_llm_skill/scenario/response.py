import json
import logging
import os
import re
import requests
import sentry_sdk
import time
import copy

from pathlib import PurePath
from typing import Any, Tuple
from common.build_dataset import build_dataset, get_text_for_candidates
import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import (
    send_request_to_prompted_generative_service,
    compose_sending_variables,
)
from df_engine.core import Context, Actor


sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_SERVICE_URL = os.getenv("GENERATIVE_SERVICE_URL")

while True:
    result = is_container_running(GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"GENERATIVE_SERVICE_URL: {GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

DOCUMENT_PROMPT_FILE = os.getenv("DOCUMENT_PROMPT_FILE")
assert GENERATIVE_SERVICE_URL, logger.error("Error: GENERATIVE_SERVICE_URL is not specified in env")
assert DOCUMENT_PROMPT_FILE, logger.error("Error: DOCUMENT_PROMPT_FILE is not specified in env")

GENERATIVE_SERVICE_CONFIG = os.getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(os.getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)

N_UTTERANCES_CONTEXT = int(os.getenv("N_UTTERANCES_CONTEXT", 3))
N_UTTERANCES_CONTEXT = (
    GENERATIVE_SERVICE_CONFIG.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
    if GENERATIVE_SERVICE_CONFIG
    else N_UTTERANCES_CONTEXT
)

FILE_SERVER_TIMEOUT = float(os.getenv("FILE_SERVER_TIMEOUT", 30))
ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
DEFAULT_SYSTEM_PROMPT = "Answer questions based on part of a text."
with open(DOCUMENT_PROMPT_FILE, "r") as f:
    DOCUMENT_PROMPT_TEXT = json.load(f)["prompt"]


FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
FIND_ID = re.compile(r"file=([0-9a-zA-Z_]*).txt")
DEFAULT_CONFIDENCE = 0.9
SUPER_CONFIDENCE = 1.0
LOW_CONFIDENCE = 0.7


def compose_data_for_model(ctx: Context, actor: Actor) -> Tuple[list, list, str]:
    if not os.path.exists("/data/documents"):
        os.mkdir("/data/documents")
    filepaths_on_server, filepaths_in_container = [], []
    final_candidates = ""
    dialog = int_ctx.get_dialog(ctx, actor)
    context = dialog.get("utterances", [])[-N_UTTERANCES_CONTEXT:]
    utterance_texts = [uttr.get("text", "") for uttr in context]
    utterances_with_doc_text = copy.deepcopy(utterance_texts)
    if utterance_texts:
        raw_candidates = context[-1].get("annotations", {}).get("doc_retriever", {}).get("candidate_files", [])
        processed_docs = context[-1].get("user", {}).get("attributes", {}).get("processed_documents", {})
        docs_in_use = context[-1].get("user", {}).get("attributes", {}).get("documents_in_use", [])
        db_link = context[-1].get("user", {}).get("attributes", {}).get("model_info", {}).get("db_link", "")
        model_id = PurePath(db_link.split("=")[-1]).stem
        if docs_in_use:
            dataset_path = f"/data/temporary_dataset_{model_id}/"
            if not os.path.exists(dataset_path):
                os.mkdir(dataset_path)
                filepaths_on_server = [
                    processed_docs[file_id].get("processed_text_link", "") for file_id in docs_in_use
                ]
                for filepath in filepaths_on_server:
                    file_id = re.search(FIND_ID, filepath).group(1)
                    filepath_container = f"/data/documents/{file_id}.txt"
                    # if we don't have doc in container, download it from server
                    if not os.path.exists(filepath_container):
                        orig_file = requests.get(filepath, timeout=FILE_SERVER_TIMEOUT)
                        with open(filepath_container, "wb") as f:
                            f.write(orig_file.content)
                    filepaths_in_container.append(filepath_container)
                logger.info(
                    f"Building dataset /data/temporary_dataset_{model_id} to get candidate texts. \
raw_candidates: {raw_candidates}, filepaths_in_container: {filepaths_in_container}, dataset_path: {dataset_path}"
                )
                build_dataset(dataset_path, filepaths_in_container)
                logger.info("Dataset built successfully")
            else:
                logger.info(f"Dataset /data/temporary_dataset_{model_id} already exists in container.")
            final_candidates = get_text_for_candidates(dataset_path, raw_candidates)
            request = utterances_with_doc_text[-1]
            utterances_with_doc_text[
                -1
            ] = f"""Text: ### {final_candidates} ###\n{DOCUMENT_PROMPT_TEXT}\nUser: {request}"""
    return utterances_with_doc_text, utterance_texts, final_candidates


def generative_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = (
        [],
        [],
        [],
        [],
        [],
    )

    def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
        nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
        if reply and confidence:
            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]

    dialog_context_to_send, dialog_context_for_logging, candidate_texts = compose_data_for_model(ctx, actor)
    hyp_attrs = {"candidate_chunks_text": candidate_texts}  # saving raw texts of candidate answers to hyp attributes
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    sending_variables = compose_sending_variables(
        {},
        ENVVARS_TO_SEND,
        human_uttr_attributes,
    )
    logger.info(f"dialog_context: {dialog_context_for_logging}")

    if len(dialog_context_to_send) > 0:
        try:
            hypotheses = send_request_to_prompted_generative_service(
                dialog_context_to_send,
                DEFAULT_SYSTEM_PROMPT,
                GENERATIVE_SERVICE_URL,
                GENERATIVE_SERVICE_CONFIG,
                GENERATIVE_TIMEOUT,
                sending_variables,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            hypotheses = []
    else:
        hypotheses = []
    logger.info(f"generated hypotheses: {hypotheses}")

    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        if len(hyp) and hyp[-1] not in [".", "?", "!"]:
            hyp += "."
            confidence = LOW_CONFIDENCE
        _curr_attrs = {
            "can_continue": CAN_NOT_CONTINUE,
        }
        _curr_attrs.update(hyp_attrs)
        gathering_responses(hyp, confidence, {}, {}, _curr_attrs)

    if len(curr_responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
