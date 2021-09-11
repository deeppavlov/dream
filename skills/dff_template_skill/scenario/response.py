from argparse import ArgumentParser
import logging
import os
import re
import sentry_sdk
import string
import time
from typing import Tuple, List, Any, Dict

from dff.core import Context, Actor
from programy.clients.args import ClientArguments
from programy.clients.client import BotClient
from programy.clients.config import ClientConfigurationData
import uuid

from dream_aiml.normalizer import PreProcessor
from state_formatters.utils import programy_post_formatter_dialog

SERVICE_NAME = os.getenv("SERVICE_NAME")

tags_map = [
    (
        re.compile("AMAZON_EMOTION_DISAPPOINTED_MEDIUM"),
        "",
        '<amazon:emotion name="disappointed" intensity="medium">',
    ),
    (
        re.compile("AMAZON_EMOTION_EXCITED_MEDIUM"),
        "",
        '<amazon:emotion name="excited" intensity="medium">',
    ),
    (re.compile("AMAZON_EMOTION_CLOSE."), "", "</amazon:emotion>"),
    (re.compile("AMAZON_EMOTION_CLOSE"), "", "</amazon:emotion>"),
]


def remove_punct(s: str) -> str:
    return "".join([c for c in s if c not in string.punctuation])


def to_dialogs(sentences: List[Any]) -> Dict[Any, Any]:
    utters = [
        {"text": sent, "user": {"user_type": "human"}} for sent in ["hi"] + sentences
    ]
    return {
        "dialogs": [
            {"utterances": utters, "bot_utterances": utters, "human_utterances": utters}
        ]
    }


def create_amazon_ssml_markup(text: str) -> Tuple[str, str]:
    untagged_text = text
    tagged_text = text
    for reg, untag, tag in tags_map:
        untagged_text = reg.sub(untag, untagged_text)
        tagged_text = reg.sub(tag, tagged_text)
    return untagged_text, tagged_text


class AIBotClient(BotClient):
    def __init__(self, botid: str, argument_parser: ArgumentParser = None):
        BotClient.__init__(self, botid, argument_parser)

    def get_client_configuration(self):
        return ClientConfigurationData("rest")

    def parse_arguments(self, argument_parser: ArgumentParser):
        client_args = AIBotArguments(self, parser=argument_parser)
        client_args.parse_args(self)
        return client_args

    def ask_question(self, userid: str, question: str, metadata: Any = None):
        response = ""
        try:
            self._questions += 1
            client_context = self.create_client_context(userid)
            response = client_context.bot.ask_question(
                client_context, question, responselogger=self
            )

        except Exception as e:
            logging.exception(e)

        return response


class AIBotArguments(ClientArguments):
    def __init__(self, client: AIBotClient, parser: ArgumentParser = None):
        self.args = None

        ClientArguments.__init__(self, client)
        self._config_name = "/src/data/config.aibot.yaml"
        self._config_format = "yaml"
        self._logging = None
        if parser is None:
            self.parser = ArgumentParser()
        else:
            self.parser = parser
        client.add_client_arguments(self.parser)

    def parse_args(self, client: AIBotClient):
        client.parse_args(self, self.args)


try:
    logging.info("Start to load model")

    model = AIBotClient("AIBot")
    preprocessor = PreProcessor(fpath="/src/data/storage/lookups/normal.txt")

    logging.info("Load model")
except Exception as e:
    logging.exception(e)
    raise (e)


def programy_reponse(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    st_time = time.time()
    question = "Unknown"
    try:
        responses = ""
        for dialog in to_dialogs(list(ctx.requests.values()))["dialogs"]:

            user_sentences = programy_post_formatter_dialog(dialog).get(
                "sentences_batch"
            )
            user_sentences = user_sentences[0] if user_sentences else [""]

            replace_phrases = ["thanks.", "thank you.", "please."]
            for phrase in replace_phrases:
                if user_sentences[-1] != phrase:
                    user_sentences[-1] = user_sentences[-1].replace(phrase, "").strip()

            userid = uuid.uuid4().hex
            # if user said let's chat at beginning of a dialogue, that we
            # should response with greeting
            answer = ""
            for _, sentence in enumerate(user_sentences):
                # s = s if i != 0 else f"BEGIN_USER_UTTER {s}"
                new_answer = model.ask_question(userid, preprocessor.process(sentence))
                if new_answer:
                    answer = f"{answer} {new_answer}"

            if "DEFAULT_SORRY_RESPONCE" in answer:
                answer = (
                    "AMAZON_EMOTION_DISAPPOINTED_MEDIUM "
                    "Sorry, I don't have an answer for that! "
                    "AMAZON_EMOTION_CLOSE"
                )

            untagged_text, ssml_tagged_text = create_amazon_ssml_markup(answer)

            responses = f"{responses} {untagged_text.strip()}"
        return responses
    except Exception as e:
        sentry_sdk.capture_exception(e)
        import traceback

        logging.error(
            f"Get exception with type {type(e)} and value {e}.\n"
            f"Traceback is {traceback.format_exc()}"
        )
        return [uuid.uuid4().hex, question, str(e)]
    finally:
        total_time = time.time() - st_time
        logging.info(f"{SERVICE_NAME} exec time = {total_time:.3f}s")
