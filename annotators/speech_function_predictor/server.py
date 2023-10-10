from typing import List
import logging
import os
import time

import sentry_sdk
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from model import init_model

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


class_dict, counters, label_to_name = init_model()


def predict(label_name):
    try:
        class_id = class_dict[label_name]
    except KeyError:
        return {}
    sorted_classes = sorted(enumerate(counters[class_id]), reverse=True, key=lambda x: x[1])
    sorted_classes = [x for x in sorted_classes if x[1] > 0]
    return [{"prediction": label_to_name[label], "confidence": probability} for label, probability in sorted_classes]


try:
    predict("Reply.Acknowledge")
    logger.info("model loaded, test query processed")
except Exception as e:
    logger.exception("model not loaded")
    sentry_sdk.capture_exception(e)
    raise e


async def handler(payload: List[str]):
    responses = [{}] * len(payload)
    try:
        responses = [predict(speech_function) for speech_function in payload]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return responses


@app.post("/model")
async def answer(payload: List[str]):
    st_time = time.time()
    responses = await handler(payload)
    total_time = time.time() - st_time
    logger.info(f"speech_function_predictor model exec time: {total_time:.3f}s")
    return responses


@app.post("/annotation")
async def annotation(payload: List[str]):
    st_time = time.time()
    responses = await handler(payload)
    total_time = time.time() - st_time
    logger.info(f"speech_function_predictor batch exec time: {total_time:.3f}s")
    return [{"batch": responses}]
