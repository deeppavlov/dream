import logging
from typing import Any, Optional

from dff.core.keywords import GRAPH, RESPONSE, PROCESSING
from dff.core import Actor, Context, Node

import common.dff.integration.response as int_rsp
from common.utils import is_toxic_or_blacklisted_utterance
from .responses import are_we_recorded_response, what_do_you_mean_response, generate_acknowledgement_response, \
    generate_universal_response, ask_for_topic_after_two_no_in_a_row_to_linkto_response
from .responses_utils import DONTKNOW_PHRASE, DONTKNOW_CONF

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)


def grounding_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    dialog = ctx.misc['agent']['dialog']
    curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

    def gathering_responces(reply, confidence, human_attr, bot_attr, attr, name):
        nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
        if reply and confidence:
            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]
            logger.info(f"Grounding skill {name}: {reply}")

    is_toxic = (
        is_toxic_or_blacklisted_utterance(dialog["human_utterances"][-2])  # ???
        if len(dialog["human_utterances"]) > 1
        else False
    )
    reply, confidence, human_attr, bot_attr, attr = are_we_recorded_response(dialog)
    gathering_responces(reply, confidence, human_attr, bot_attr, attr, "are_we_recorded")

    if not is_toxic:
        reply, confidence, human_attr, bot_attr, attr = what_do_you_mean_response(dialog)
        gathering_responces(reply, confidence, human_attr, bot_attr, attr, "what_do_you_mean")

    reply, confidence, human_attr, bot_attr, attr = generate_acknowledgement_response(dialog)
    gathering_responces(reply, confidence, human_attr, bot_attr, attr, "acknowledgement_response")

    reply, confidence, human_attr, bot_attr, attr = generate_universal_response(dialog)
    gathering_responces(reply, confidence, human_attr, bot_attr, attr, "universal_response")

    reply, confidence, human_attr, bot_attr, attr = ask_for_topic_after_two_no_in_a_row_to_linkto_response(dialog)
    gathering_responces(reply, confidence, human_attr, bot_attr, attr, '2 "no" detected')

    # to pass assert  "Got empty replies"
    if len(curr_responses):
        gathering_responces(DONTKNOW_PHRASE, DONTKNOW_CONF, {}, {}, {}, "dont_know_response")

    return int_rsp.multi_response(replies=curr_responses,
                                  confidences=curr_confidences,
                                  human_attr=curr_human_attrs,
                                  bot_attr=curr_bot_attrs,
                                  hype_attr=curr_attrs,
                                  )


def call_processing(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
) -> Optional[tuple[str, Node]]:
    logger.info(f'node.response {node.response}')
    if callable(node.response):
        node.response = node.response(ctx, actor, *args, **kwargs)
    else:
        node.response = node.response
    return node_label, node


flows = {
    "grounding": {
        GRAPH: {
            "grounding_response_node": {
                RESPONSE: grounding_response,
                PROCESSING: call_processing,
            },
        }
    },
}

actor = Actor(flows, start_node_label=("grounding", "grounding_response_node"),
              fallback_node_label=("grounding", "grounding_response_node"))
