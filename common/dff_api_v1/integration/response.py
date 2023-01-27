import logging
from typing import Union, Optional

from dff.script import Context, Actor, Message, MultiMessage


logger = logging.getLogger(__name__)
DEFAULT_CONFIDENCE = 0.0


def multi_response(
    replies: list[str],
    confidences: Optional[list] = None,
    human_attr: Union[list, dict] = {},
    bot_attr: Union[list, dict] = {},
    hype_attr: Union[list, dict] = {},
):
    assert replies, "Got empty replies"
    assert not isinstance(confidences, list) or len(confidences) == len(replies)
    assert not isinstance(human_attr, list) or len(human_attr) == len(replies)
    assert not isinstance(bot_attr, list) or len(bot_attr) == len(replies)
    assert not isinstance(hype_attr, list) or len(hype_attr) == len(replies)
    confidences = confidences if confidences is not None else [DEFAULT_CONFIDENCE] * len(replies)
    human_attr = human_attr if isinstance(human_attr, list) else [human_attr] * len(replies)
    bot_attr = bot_attr if isinstance(bot_attr, list) else [bot_attr] * len(replies)
    hype_attr = hype_attr if isinstance(hype_attr, list) else [hype_attr] * len(replies)

    def multi_response_handler(ctx: Context, actor: Actor) -> list:
        return MultiMessage(
            messages=[
                Message(
                    text=reply,
                    misc={"confidence": confidence, "human_attr": human_at, "bot_attr": bot_at, "hype_attr": hype_at},
                )
                for reply, confidence, human_at, bot_at, hype_at in zip(
                    replies, confidences, human_attr, bot_attr, hype_attr
                )
            ]
        )

    return multi_response_handler
