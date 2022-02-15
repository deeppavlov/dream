import logging
import requests
import sentry_sdk
from os import getenv
from typing import Any

import common.dff.integration.response as int_rsp
from df_engine.core import Context, Actor
from common.constants import CAN_NOT_CONTINUE


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
DIALOGPT_SERVICE_URL = getenv("DIALOGPT_SERVICE_URL")
assert DIALOGPT_SERVICE_URL


def compose_data_for_dialogpt(dialog):
    data = []
    # for uttr in dialog["utterances"][-3:]:
    #     curr_uttr = {"speaker": uttr["user"]["user_type"], "text": uttr["text"]}
    #     data.append(curr_uttr)
    if len(dialog["human_utterances"]) > 1:
        data += [{"speaker": dialog["human_utterances"][-2]["user"]["user_type"],
                  "text": dialog["human_utterances"][-2]["text"]}]

    if len(dialog["bot_utterances"]) > 0:
        data += [{"speaker": dialog["bot_utterances"][-1]["user"]["user_type"],
                  "text": dialog["bot_utterances"][-1]["text"]}]

    data += [{"speaker": dialog["human_utterances"][-1]["user"]["user_type"],
              "text": dialog["human_utterances"][-1]["text"]}]

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

    request_data = compose_data_for_dialogpt(ctx.misc["agent"]["dialog"])
    hypotheses = requests.post(
        DIALOGPT_SERVICE_URL, json={"dialog_contexts": [request_data]}, timeout=1).json()["generated_responses"][0]

    for hyp in hypotheses:
        reply, confidence, human_attr, bot_attr, attr = hyp, 0.95, {}, {}, {"can_continue": CAN_NOT_CONTINUE}
        gathering_responses(reply, confidence, human_attr, bot_attr, attr)

    if len(curr_responses) == 0:
        gathering_responses("", 0.01, {}, {}, {})
    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
