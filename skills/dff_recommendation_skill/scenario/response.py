import logging
import requests
import sentry_sdk
from os import getenv
from typing import Any
import random

import common.dff.integration.response as int_rsp
import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
from df_engine.core import Context, Actor
from common.constants import CAN_CONTINUE_SCENARIO


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
INFILLING = getenv("INFILLING")
DIALOGPT_RESPOND = getenv("DIALOGPT_RESPOND_ENG_SERVICE_URL")
assert INFILLING


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def compose_data_for_infilling(ctx, actor): # ПОКА ЧТО ТРИ ПРОШЛЫЕ РЕПЛИКИ, ДОДЕЛАТЬ
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

def generate_infilling_response(prompts=['_']):
    reply = random.choice(prompts)

    def infilling_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"dff-recommendation-skill: {reply}")
    
        request_data = compose_data_for_infilling(ctx, actor)
        previous_context = ' '.join([x['text'] for x in request_data])
        request_data = {"texts": [previous_context + ' ' + reply]}
        if len(request_data) > 0:
            response = requests.post(INFILLING, json=request_data).json()
            hypothesis = [response["infilled_text"][0].replace(previous_context, '')]
        else:
            hypothesis = []

        for hyp in hypothesis:
            # if hyp[-1] not in [".", "?", "!"]:
            #     hyp += "."
            gathering_responses(hyp, 0.99, {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})

        #ctx = int_prs.save_slots_to_ctx({"recommendation": hypothesis[0]})(ctx, actor) #как сделать чтоб это работало? Диля

        if len(curr_responses) == 0:
            return ""

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)
    return infilling_response



def compose_data_for_dialogpt(ctx, actor):
    data = []
    # for uttr in dialog["utterances"][-3:]:
    #     curr_uttr = {"speaker": uttr["user"]["user_type"], "text": uttr["text"]}
    #     data.append(curr_uttr)

    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    bot_uttrs = int_ctx.get_bot_utterances(ctx, actor)

    if len(human_uttrs) > 1:
        data.append(human_uttrs[-2]["text"])
    if len(bot_uttrs) > 0:
        data.append(bot_uttrs[-1]["text"])
    if len(human_uttrs) > 0:
        data.append(human_uttrs[-1]["text"])

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
        #response = requests.post(DIALOGPT_RESPOND, json={"dialog_contexts": [request_data]}, timeout=5) #допишу свой урл
        result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
        hypotheses = result[0]
    else:
        hypotheses = []
    return str(hypotheses)
    # for hyp in hypotheses:
    #     if hyp[-1] not in [".", "?", "!"]:
    #         hyp += "."
    #     gathering_responses(hyp, 0.99, {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
    # if len(curr_responses) == 0:
    #     return ""

    # return int_rsp.multi_response(
    #     replies=curr_responses,
    #     confidences=curr_confidences,
    #     human_attr=curr_human_attrs,
    #     bot_attr=curr_bot_attrs,
    #     hype_attr=curr_attrs,
    # )(ctx, actor, *args, **kwargs)
