from argparse import ArgumentParser
import logging
import os
import re
from typing import Tuple, Any

from dff.core import Context, Actor
from programy.clients.args import ClientArguments
from programy.clients.client import BotClient
from programy.clients.config import ClientConfigurationData
import uuid

from utils.normalizer import PreProcessor

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
            response = client_context.bot.ask_question(client_context, question, responselogger=self)

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
    # user_sentences = user_sentences[0] if user_sentences else [""]

    # replace_phrases = ["thanks.", "thank you.", "please."]
    # for phrase in replace_phrases:
    #     if user_sentences[-1] != phrase:
    #         user_sentences[-1] = user_sentences[-1].replace(phrase, "").strip()

    userid = uuid.uuid4().hex
    # if user said let's chat at beginning of a dialogue, that we
    # should response with greeting
    response = ""
    for _, sentence in enumerate(ctx.requests.values()):
        # s = s if i != 0 else f"BEGIN_USER_UTTER {s}"
        response = model.ask_question(userid, preprocessor.process(sentence))

    # if "DEFAULT_SORRY_RESPONCE" in response:
    #     response = (
    #         "AMAZON_EMOTION_DISAPPOINTED_MEDIUM "
    #         "Sorry, I don't have an answer for that! "
    #         "AMAZON_EMOTION_CLOSE"
    #     )

    # untagged_text, ssml_tagged_text = create_amazon_ssml_markup(answer)

    # responses = f"{responses} {untagged_text.strip()}"
    return response
