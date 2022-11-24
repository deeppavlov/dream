import logging
import os
import pathlib

from df_engine.core import Context, Actor

from common.constants import CAN_NOT_CONTINUE
from common.dff.integration.context import set_confidence, set_can_continue
from common.programy.model import get_programy_model
from common.sensitive import psycho_help_spec


logger = logging.getLogger(__name__)
LANGUAGE = os.getenv("LANGUAGE", "EN")
model_folder = "data_ru" if LANGUAGE == "RU" else "data"
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
    if psycho_help_spec in response:
        set_confidence(ctx, actor, 0.85)
        set_can_continue(ctx, actor, continue_flag=CAN_NOT_CONTINUE)
        return response
    return response
