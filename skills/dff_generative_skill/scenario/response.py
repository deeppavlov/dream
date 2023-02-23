import logging
import re
import requests
import sentry_sdk
from os import getenv
from typing import Any

import common.dff.integration.response as int_rsp
import common.dff.integration.context as int_ctx
from df_engine.core import Context, Actor
from common.constants import CAN_NOT_CONTINUE


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
assert GENERATIVE_SERVICE_URL


FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
GENERATIVE_TIMEOUT = 4
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.5


def compose_data_for_model(ctx, actor):
    data = []
    # for uttr in dialog["utterances"][-3:]:
    #     curr_uttr = {"speaker": uttr["user"]["user_type"], "text": uttr["text"]}
    #     data.append(curr_uttr)

    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    bot_uttrs = int_ctx.get_bot_utterances(ctx, actor)

    if len(human_uttrs) > 1:
        data += [{"speaker": human_uttrs[-2]["user"]["user_type"], "text": human_uttrs[-2]["text"]}]

    if len(bot_uttrs) > 0:
        data += [{"speaker": bot_uttrs[-1]["user"]["user_type"], "text": bot_uttrs[-1]["text"]}]
    if len(human_uttrs) > 0:
        data += [{"speaker": human_uttrs[-1]["user"]["user_type"], "text": human_uttrs[-1]["text"]}]

    return data


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

    request_data = compose_data_for_model(ctx, actor)
    logger.info(f"request_data: {request_data}")
    if len(request_data) > 0:
        response = requests.post(
            GENERATIVE_SERVICE_URL,
            json={"dialog_contexts": [request_data]},
            timeout=3.8,
        )
        hypotheses = response.json()[0]
    else:
        hypotheses = []
    logger.info(f"hyps: {hypotheses}")
    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        hyp_text = " ".join(hyp.split())
        if len(hyp_text) and hyp_text[-1] not in [".", "?", "!"]:
            hyp_text += "."
            confidence = LOW_CONFIDENCE
        gathering_responses(hyp_text, confidence, {}, {}, {"can_continue": CAN_NOT_CONTINUE})

    if len(curr_responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
