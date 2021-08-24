"""
Copyright (c) 2016-2019 Keith Sterling http://www.keithsterling.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import json
import random
import logging
from os import getenv
import re
import string
import time
from typing import Tuple, List, Any

from fastapi import FastAPI
from programy.services.coordinator import RandomResultServiceCoordinator
from pydantic import BaseModel
import sentry_sdk
from starlette.middleware.cors import CORSMiddleware
import uuid

from common.dialogflow_framework.programy.model import (
    get_programy_model,
    get_configuration_files,
)
from dream_aiml.normalizer import PreProcessor
from state_formatters.utils import programy_post_formatter_dialog
import test_server


SERVICE_NAME = getenv("SERVICE_NAME")
RANDOM_SEED = int(getenv("RANDOM_SEED", 2718))
CONFIG_PATH = getenv("CONFIG_PATH", "/src/data/config.json")
sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    force=True,
)
logger = logging.getLogger(__name__)

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


class User(BaseModel):
    user_type: str


class Utterance(BaseModel):
    text: str
    user: User


class BotUtterance(BaseModel):
    text: str
    user: User


class HumanUtterance(BaseModel):
    text: str
    user: User


class Dialog(BaseModel):
    utterances: List[Utterance]
    bot_utterances: List[BotUtterance]
    human_utterances: List[HumanUtterance]


class RequestModel(BaseModel):
    dialogs: List[Dialog]


def remove_punct(s: str) -> str:
    return "".join([c for c in s if c not in string.punctuation])


def create_amazon_ssml_markup(text: str) -> Tuple[str, str]:
    untagged_text = text
    tagged_text = text
    for reg, untag, tag in tags_map:
        untagged_text = reg.sub(untag, untagged_text)
        tagged_text = reg.sub(tag, tagged_text)
    return untagged_text, tagged_text


def handler(requested_data: RequestModel, random_seed: Any = None) -> List[Any]:
    st_time = time.time()
    question = "Unknown"
    try:
        responses = []
        if random_seed is not None:
            random.seed(random_seed)
        for dialog in requested_data["dialogs"]:

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
                logger.info(
                    f"Sentence {sentence}. \nPreprocessor {preprocessor.process(sentence)}"
                )
                sentence_answer = model.ask_question(
                    userid, preprocessor.process(sentence)
                )
                if sentence_answer:
                    answer += sentence_answer
                logger.info(f"Answer {answer}")

            if "DEFAULT_SORRY_RESPONCE" in answer:
                answer = (
                    "AMAZON_EMOTION_DISAPPOINTED_MEDIUM "
                    "Sorry, I don't have an answer for that! "
                    "AMAZON_EMOTION_CLOSE"
                )

            untagged_text, ssml_tagged_text = create_amazon_ssml_markup(answer)

            if null_response.lower() in untagged_text.lower():
                confidence = 0.2
            elif "unknown" in untagged_text.lower():
                confidence = 0.0
                untagged_text = ""
            elif len(untagged_text.split()) <= 3:
                confidence = 0.6
            elif (
                "this is an Alexa Prize Socialbot" in untagged_text
                and len(user_sentences) > 2
            ):
                confidence = 0.6
            elif untagged_text:
                confidence = 0.98
            else:
                confidence = 0
            logger.info(
                f"user_id: {userid}; user_sentences: {user_sentences}; "
                f"curr_user_sentence: {user_sentences[-1]}; "
                f"answer: {untagged_text}; "
                f"ssml_tagged_text: {ssml_tagged_text}"
            )

            responses.append(
                [
                    untagged_text.strip(),
                    confidence,
                    {"ssml_tagged_text": ssml_tagged_text},
                ]
            )
        return responses
    except Exception as e:
        sentry_sdk.capture_exception(e)
        import traceback

        logger.error(
            f"Get exception with type {type(e)} and value {e}.\n"
            f"Traceback is {traceback.format_exc()}"
        )
        return [uuid.uuid4().hex, question, str(e)]
    finally:
        total_time = time.time() - st_time
        logger.info(f"{SERVICE_NAME} exec time = {total_time:.3f}s")


try:
    logger.info("Start to load model")
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    configuration_files = get_configuration_files(**config["program-y"])
    model = get_programy_model(configuration_files)
    preprocessor = PreProcessor(fpath=config["preprocessor"])
    null_response = config["null_response"]

    logger.info("Load model")
except Exception as e:
    logger.exception(e)
    raise (e)

try:
    # Remove random seed from RandomResultServiceCoordinator._get_servicen
    def _get_servicen(self):
        servicen = random.randint(0, len(self._services) - 1)
        return self._services[servicen]

    RandomResultServiceCoordinator._get_servicen = _get_servicen

    test_server.run_test(handler)

    logger.info(f"{SERVICE_NAME} is loaded successfully")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/respond")
async def ask(request: RequestModel):
    rest_response = handler(request.dict())
    return rest_response


@app.get("/healthcheck")
async def healthcheck():
    return "Ok"
