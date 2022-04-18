import logging
import sentry_sdk
from os import getenv

from df_engine.core import Context, Actor

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def is_sf(sf_name="Open.Give.Opinion"):
    def is_sf_handler(ctx: Context, actor: Actor, *args, **kwargs):
        try:
            last_utterance = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", {})[-1]
            utterance_sfcs = last_utterance.get("annotations", {}).get("speech_function_classifier", [])
        except KeyError:
            utterance_sfcs = []

        return sf_name in utterance_sfcs

    return is_sf_handler


def is_ext_sf(ext_sf_name="React.Respond.Support.Reply.Agree"):
    def is_ext_sf_handler(ctx: Context, actor: Actor, *args, **kwargs):
        return ext_sf_name in ctx.misc.get("ext_sf", [[]])[-1]

    return is_ext_sf_handler
    

def is_midas(midas_name="pos_answer", threshold=0.5):
    def is_midas_handler(ctx: Context, actor: Actor, *args, **kwargs):
        try:
            last_utterance = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", {})[-1]
            midas = last_utterance.get('annotations', {}).get('midas_classification', [{}])[-1]
            midas_keys = [key for key, val in midas.items() if val > threshold]
        except KeyError:
            midas_keys = []
        return midas_name in midas_keys

    return is_midas_handler


speech_functions = is_sf
