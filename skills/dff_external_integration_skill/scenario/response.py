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
# можно сделать фейковый сервис либо на серваке через прокси поднимаю агента и отдельно скилл (в разных окнах) 
EXTERNAL_SKILL_URL = "0.0.0.0:4242/chat" #посмотреть как добавить
ARGUMENT_TO_SEND = getenv("ARGUMENT_TO_SEND", "message")
RESPONSE_KEY = getenv("RESPONSE_KEY", None)

assert "EXTERNAL_SKILL_URL", logger.info("You need to provide the external skill url to get its responses.")

def get_external_skill_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        try:
            dialog = int_ctx.get_dialog(ctx, actor)
            dialog_id = dialog.get("dialog_id", "unknown")
            message_text = dialog.get("human_utterances", [{}])[-1].get("text", "")
            payload = {"dialog_id": dialog_id, ARGUMENT_TO_SEND: message_text}
            if RESPONSE_KEY:
                response = requests.post(EXTERNAL_SKILL_URL, json=payload).json()[RESPONSE_KEY]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            response = ""
        return response
    else:
        response = ""
