import logging
import os
import time
from typing import Optional, List

import sentry_sdk
from fastapi import FastAPI
from nltk import sent_tokenize
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from models import get_speech_function

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Payload(BaseModel):
    phrase: List[str]
    prev_phrase: Optional[str]
    prev_speech_function: Optional[str]


class AnnotationPayload(BaseModel):
    phrase: str
    prev_phrase: Optional[str]
    prev_speech_function: Optional[str]


try:
    speech_function = get_speech_function("fine, thank you", "How are you doing?", "Open.Demand.Fact.")
    logger.info(speech_function)
    logger.info("model loaded, test query processed")
except Exception as e:
    logger.exception("model not loaded")
    sentry_sdk.capture_exception(e)
    raise e


async def handler(payload: List[Payload]):
    responses = [""] * len(payload)
    try:
        for i, p in enumerate(payload):
            phrase_len = len(p.phrase)
            phrases = [p.prev_phrase] + p.phrase
            authors = ["John"] + ["Doe"] * phrase_len
            response = [p.prev_speech_function]
            for phr, prev_phr, auth, prev_auth in zip(phrases[1:], phrases[:-1], authors[1:], authors[:-1]):
                speech_f = get_speech_function(phr, prev_phr, response[-1], auth, prev_auth)
                response.append(speech_f)
            responses[i] = response[1:]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return responses


@app.post("/model")
async def answer(payload: Payload):
    st_time = time.time()
    responses = await handler([payload])
    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier model exec time: {total_time:.3f}s")
    return responses


@app.post("/annotation")
async def annotation(payload: List[AnnotationPayload]):
    st_time = time.time()
    responses = await handler(
        [
            Payload(
                phrase=sent_tokenize(p.phrase),
                prev_phrase=p.prev_phrase,
                prev_speech_function=p.prev_speech_function,
            )
            for p in payload
        ]
    )
    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier batch exec time: {total_time:.3f}s")
    return [{"batch": responses}]
