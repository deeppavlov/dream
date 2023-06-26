import json
import logging
import re
import sentry_sdk
from os import getenv
import os
from typing import Any, List
import requests

from common.build_dataset import build_dataset
import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.prompts import (
    send_request_to_prompted_generative_service,
    compose_sending_variables,
)
from df_engine.core import Context, Actor


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")  # add env!!!
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
DEFAULT_PROMPT = "Answer questions based on part of a text."
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")

assert GENERATIVE_SERVICE_URL

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
FIND_ID = re.compile(r"file=([0-9a-zA-Z]*).txt")
DEFAULT_CONFIDENCE = 0.9
SUPER_CONFIDENCE = 1.0
LOW_CONFIDENCE = 0.7


def get_text_for_candidates(dataset_path: str, raw_candidates: List[str]) -> str:
    num_candidates = []
    nums = 0
    for f_name in raw_candidates:
        nums += 1
        with open(dataset_path + f_name) as f:
            num_candidates.append(f"{nums}. {f.read()}")
    return " ".join(num_candidates)


def compose_data_for_model(ctx: Context, actor: Actor) -> str:
    if not os.path.exists("/data/documents"):
        os.mkdir("/data/documents")
    dialog = int_ctx.get_dialog(ctx, actor)
    context = dialog.get("utterances", [])[-N_UTTERANCES_CONTEXT:]
    utterance_texts = [uttr.get("text", "") for uttr in context]
    if utterance_texts:
        raw_candidates = context[-1].get("annotations", {}).get("doc_retriever", {}).get("candidate_files", [])
        filepaths_on_server = (
            context[-1].get("user", {}).get("attributes", {}).get("documents_qa_model", {}).get("document_links", [])
        )
        filepaths_in_container = []
        for filepath in filepaths_on_server:
            file_id = re.search(FIND_ID, filepath).group(1)
            filepath_container = f"/data/documents/{file_id}.txt"
            orig_file = requests.get(filepath, timeout=30)
            with open(filepath_container, "wb") as f:
                f.write(orig_file.content)
            filepaths_in_container.append(filepath_container)
        dataset_path = "/data/temporary_dataset/"
        if not os.path.exists(dataset_path):
            os.mkdir(dataset_path)
        logger.info(
            f"""Building dataset to get candidate texts. raw_candidates: {raw_candidates},
filepaths_in_container: {filepaths_in_container}, dataset_path: {dataset_path}"""
        )
        build_dataset(dataset_path, filepaths_in_container)
        logger.info("Dataset built successfully")
        final_candidates = get_text_for_candidates(dataset_path, raw_candidates)
        request = utterance_texts[-1]
        utterance_texts[
            -1
        ] = f"""Text: ### {final_candidates} ###
USER: {request}
Reply to USER. If USER asks a question, answer based on Text that contains some information about the subject.
If necessary, structure your answer as bullet points. You may also present information in tables.
If text does not contain the answer, apologize and say that you cannot answer based on the given text.
Only answer the question asked, do not include additional information. Text may contain unrelated information.
Do not provide sources. """
    return utterance_texts


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

    dialog_context = compose_data_for_model(ctx, actor)
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
    lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
    envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
    sending_variables = compose_sending_variables(
        lm_service_kwargs,
        envvars_to_send,
        **human_uttr_attributes,
    )

    logger.info(f"dialog_context: {dialog_context}")
    if len(dialog_context) > 0:
        try:
            hypotheses = send_request_to_prompted_generative_service(
                dialog_context,
                DEFAULT_PROMPT,
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
        _curr_attrs = {"can_continue": CAN_NOT_CONTINUE}
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
