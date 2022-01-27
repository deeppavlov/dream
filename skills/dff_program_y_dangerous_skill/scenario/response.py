import os
import logging

from df_engine.core import Context, Actor

from common.programy.model import get_programy_model

logger = logging.getLogger(__name__)

LANGUAGE = os.environ.get("LANGUAGE")
DATA_FOLDER = "data_ru" if LANGUAGE == "RUSSIAN" else "data"

try:
    logger.info("Start to load model")
    model = get_programy_model(DATA_FOLDER)
    logger.info("Load model")
except Exception as e:
    logger.exception(e)
    raise (e)


def programy_reponse(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = model(ctx.requests.values())
    return response
