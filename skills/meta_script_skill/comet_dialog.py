#!/usr/bin/env python

import logging
from os import getenv
import sentry_sdk

from utils import get_used_attributes_by_name
from comet_responses import ask_question_using_atomic, comment_using_atomic, express_opinion_using_conceptnet
from constants import MAX_NUMBER_OF_HYPOTHESES_BY_SKILL


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def respond_comet_dialog(dialogs_batch):
    final_responses = []
    final_confidences = []
    final_attributes = []

    for dialog in dialogs_batch:
        curr_responses = []
        curr_confidences = []
        curr_attrs = []

        comet_dialog_status = get_used_attributes_by_name(
            dialog["utterances"][-3:], attribute_name="atomic_dialog",
            value_by_default=None, activated=True, skill_name="comet_dialog_skill")
        if len(comet_dialog_status) > 0 and comet_dialog_status[-1] == "ask_question" and \
                "?" not in dialog["human_utterances"][-1]["text"]:
            logger.info(f"Found previous comet dialog status: {comet_dialog_status}")
            responses, confidences, attrs = comment_using_atomic(dialog)
        else:
            responses, confidences, attrs = ask_question_using_atomic(dialog)

        logger.info(f"Comet dialog hypotheses: {list(zip(responses, confidences, attrs))}")
        curr_responses.extend(responses)
        curr_confidences.extend(confidences)
        curr_attrs.extend(attrs)

        responses, confidences, attrs = express_opinion_using_conceptnet(dialog)
        logger.info(f"Comet opinion hypotheses: {list(zip(responses, confidences, attrs))}")
        curr_responses.extend(responses)
        curr_confidences.extend(confidences)
        curr_attrs.extend(attrs)

        sorted_pairs = sorted(zip(curr_responses, curr_confidences, curr_attrs),
                              key=lambda x: x[1], reverse=True)[:MAX_NUMBER_OF_HYPOTHESES_BY_SKILL]
        curr_responses, curr_confidences, curr_attrs = [pair[0] for pair in sorted_pairs], \
                                                       [pair[1] for pair in sorted_pairs], \
                                                       [pair[2] for pair in sorted_pairs]

        # here will be other variants
        final_responses.append(curr_responses)
        final_confidences.append(curr_confidences)
        final_attributes.append(curr_attrs)

    return final_responses, final_confidences, final_attributes
