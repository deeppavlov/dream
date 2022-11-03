import logging
from typing import Union, List
import random
from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def multi_response(
    replies: List[str],
    confidences: Union[list, float] = 0.0,
    human_attr: Union[list, dict] = {},
    bot_attr: Union[list, dict] = {},
    hype_attr: Union[list, dict] = {},
):
    assert replies, "Got empty replies"
    assert not isinstance(confidences, list) or len(confidences) == len(replies)
    assert not isinstance(human_attr, list) or len(human_attr) == len(replies)
    assert not isinstance(bot_attr, list) or len(bot_attr) == len(replies)
    assert not isinstance(hype_attr, list) or len(hype_attr) == len(replies)
    confidences = confidences if isinstance(confidences, list) else [confidences] * len(replies)
    human_attr = human_attr if isinstance(human_attr, list) else [human_attr] * len(replies)
    bot_attr = bot_attr if isinstance(bot_attr, list) else [bot_attr] * len(replies)
    hype_attr = hype_attr if isinstance(hype_attr, list) else [hype_attr] * len(replies)

    def multi_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> list:
        hyps = [hyp for hyp in zip(replies, confidences, human_attr, bot_attr, hype_attr)]
        random.shuffle(hyps)
        return hyps

    return multi_response_handler
