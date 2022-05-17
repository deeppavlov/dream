import logging
import re
import common.dff.integration.context as int_ctx
from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def get_destination():
    def get_destination_handler(ctx: Context, actor: Actor, *args, **kwargs):
        utt = int_ctx.get_last_human_utterance(Context, Actor)
        results = re.findall(r"(?:(?:go to)|(?:move to)|(?:come to)) (\d+)\,*\s*(\d+)\,*\s*(\d+)", utt)
        return (results[0][0], results[0][1], results[0][2])
    return get_destination_handler
