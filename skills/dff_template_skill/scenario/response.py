import logging

from dff.core import Context, Actor

from common.programy.model import get_programy_model

logger = logging.getLogger(__name__)

try:
    logger.info("Start to load model")
    model = get_programy_model("data")
    logger.info("Load model")
except Exception as e:
    logger.exception(e)
    raise (e)


def programy_reponse(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = model(ctx.requests.values())
    return response
