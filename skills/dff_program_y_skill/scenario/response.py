import logging
import os
import pathlib

from df_engine.core import Context, Actor

from common.programy.model import get_programy_model

logger = logging.getLogger(__name__)
LANGUAGE = os.getenv("LANGUAGE", "ENGLISH")
model_folder = "data_ru" if LANGUAGE == "RUSSIAN" else "data"
logger.info(f"Selected dff-program-y-skill: {LANGUAGE} language.")

try:
    logger.info("Start to load model")
    model = get_programy_model(pathlib.Path(model_folder))
    logger.info("Load model")
except Exception as e:
    logger.exception(e)
    raise (e)


def programy_reponse(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = model(ctx.requests.values())
    return response
