import json
import logging
import re
import requests
import sentry_sdk
from os import getenv
from typing import Any

from common.build_dataset import build_dataset
import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from df_engine.core import Context, Actor


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 120))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))
FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7
DEFAULT_PROMPT = "Answer questions based on part of a text."
CONSIDERED_LM_SERVICES = {
    "ChatGPT": {
        "url": "http://openai-api-chatgpt:8145/respond",
        "config": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
        "envvars_to_send": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    }
}


def compose_data_for_model(ctx, actor):
    context = int_ctx.get_utterances(ctx, actor)[-N_UTTERANCES_CONTEXT:]
    utterance_texts = [uttr.get("text", "") for uttr in context]
    if utterance_texts:
        with open("test_annotations.json", "w") as f:
            json.dump(context[-1].get("annotations", {}), f)
        raw_candidates = (
            context[-1]
            .get("annotations", {})
            .get("doc_retriever", {})
            .get("candidate_files", [])
        )
        ORIGINAL_FILE_PATH = (
            context[-1]
            .get("annotations", {})
            .get("doc_retriever", {})
            .get("file_path", "")
        )
        DATASET_PATH = (
            context[-1]
            .get("annotations", {})
            .get("doc_retriever", {})
            .get("dataset_path", "")
        )
        logger.info(
            f"""Building dataset to get candidate texts. raw_candidates: {raw_candidates},
            ORIGINAL_FILE_PATH: {ORIGINAL_FILE_PATH}, DATASET_PATH: {DATASET_PATH}"""
        )
        build_dataset(DATASET_PATH, ORIGINAL_FILE_PATH)
        num_candidates = []
        nums = 0
        for f_name in raw_candidates:
            nums += 1
            with open(DATASET_PATH + f_name) as f:
                num_candidates.append(f"{nums}. {f.read()}")
        final_candidates = " ".join(num_candidates)
        request = utterance_texts[-1]
        logger.info("Dataset built successfully")
        utterance_texts[
            -1
        ] = f"""TEXT: ### {final_candidates} ###
USER: {request}
Reply to USER. If USER makes a request or asks a question, answer based on TEXT provided.
If necessary, structure your answer as bullet points. You may also present information in tables.
If TEXT does not contain the answer, apologize and say that you cannot answer based on the given text."""
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
    logger.info(f"dialog_context: {dialog_context}")
    lm_service = "ChatGPT"
    if "envvars_to_send" in CONSIDERED_LM_SERVICES[lm_service]:
        sending_variables = {
            f"{var.lower()}s": [getenv(var, None)]
            for var in CONSIDERED_LM_SERVICES[lm_service]["envvars_to_send"]
        }
        if len(sending_variables.keys()) > 0 and all(
            [var_value is None for var_value in sending_variables.values()]
        ):
            raise NotImplementedError(
                "ERROR: All environmental variables have None values. At least one of them must have not None value"
            )
    else:
        sending_variables = {}
    if len(dialog_context) > 0:
        try:
            response = requests.post(
                CONSIDERED_LM_SERVICES[lm_service]["url"],
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [DEFAULT_PROMPT],
                    "configs": [CONSIDERED_LM_SERVICES[lm_service]["config"]],
                    **sending_variables,
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            hypotheses = response.json()[0]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            hypotheses = []
    else:
        hypotheses = []
    logger.info(f"generated hypotheses: {hypotheses}")
    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        hyp_text = " ".join(hyp.split())
        if len(hyp_text) and hyp_text[-1] not in [".", "?", "!"]:
            hyp_text += "."
            confidence = LOW_CONFIDENCE
        gathering_responses(
            hyp_text, confidence, {}, {}, {"can_continue": CAN_NOT_CONTINUE}
        )

    if len(curr_responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
