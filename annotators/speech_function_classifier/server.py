import pickle
from typing import Optional, List
import logging
import os
import time

import sentry_sdk
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from models import get_features

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


class Payload(BaseModel):
    bot_utterance: Optional[str]
    human_utterance: str


with open("logreg.pickle", "rb") as f:
    model = pickle.load(f)


try:
    input_features = np.concatenate([get_features("Hi", "How are you")])
    logger.info(model.predict_proba(input_features))
    logger.info("model loaded, test query processed")
except Exception as e:
    logger.exception("model not loaded")
    sentry_sdk.capture_exception(e)
    raise e


async def handler(payload: List[Payload]):
    responses = [{}] * len(payload)
    try:
        input_features = np.concatenate([get_features(p.human_utterance, p.bot_utterance) for p in payload])
        probas = model.predict_proba(input_features)
        responses = [{"type": model.classes_[proba.argmax()], "confidence": proba.max()} for proba in probas]
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
async def annotation(payload: List[Payload]):
    st_time = time.time()
    responses = await handler(payload)
    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier batch exec time: {total_time:.3f}s")
    return [{"batch": responses}]
