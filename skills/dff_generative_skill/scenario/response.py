import logging
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
DIALOGPT_SERVICE_URL = getenv("DIALOGPT_SERVICE_URL")
assert DIALOGPT_SERVICE_URL


def compose_data_for_dialogpt(ctx, actor):
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
    curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

    def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
        nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
        if reply and confidence:
            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]
            logger.info(f"dff-generative-skill: {reply}")

    request_data = compose_data_for_dialogpt(ctx, actor)
    if len(request_data) > 0:
        response = requests.post(DIALOGPT_SERVICE_URL, json={"dialog_contexts": [request_data]}, timeout=3.8)
        hypotheses = response.json()["generated_responses"][0]
    else:
        hypotheses = []

    for hyp in hypotheses:
        if hyp[-1] not in [".", "?", "!"]:
            hyp += "."
        gathering_responses(hyp, 0.99, {}, {}, {"can_continue": CAN_NOT_CONTINUE})

    if len(curr_responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
