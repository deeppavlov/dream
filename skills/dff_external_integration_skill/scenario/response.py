import logging
import sentry_sdk
import requests
from os import getenv

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

EXTERNAL_SKILL_URL = getenv("EXTERNAL_SKILL_URL", None)
ARGUMENT_TO_SEND = getenv("ARGUMENT_TO_SEND", "message")

assert "EXTERNAL_SKILL_URL", logger.info("You need to provide the external skill url to get its responses.")

def get_external_skill_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        try:
            dialog = int_ctx.get_dialog(ctx, actor)
            dialog_id = dialog.get("dialog_id", "unknown")
            message_text = dialog.get("human_utterances", [{}])[-1].get("text", "")
            payload = {"dialog_id": dialog_id, ARGUMENT_TO_SEND: message_text}
            response = requests.post(EXTERNAL_SKILL_URL, params=payload)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
        return response
