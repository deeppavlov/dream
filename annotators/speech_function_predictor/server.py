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
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

class_dict, counters, label_to_name = init_model()

full_labels = [
    "Open.Attend",
    "Open.Demand.Fact",
    "Open.Demand.Opinion",
    "Open.Give.Fact",
    "Open.Give.Opinion",
    "React.Rejoinder.Confront.Challenge.Counter",
    "React.Rejoinder.Confront.Response.Re-challenge",
    "React.Rejoinder.Support.Challenge.Rebound",
    "React.Rejoinder.Support.Develop.Elaborate",
    "React.Rejoinder.Support.Response.Resolve",
    "React.Rejoinder.Support.Track.Check",
    "React.Rejoinder.Support.Track.Clarify",
    "React.Rejoinder.Support.Track.Confirm",
    "React.Rejoinder.Support.Track.Probe",
    "React.Respond.Confront.Disengage",
    "React.Respond.Confront.Reply.Contradict",
    "React.Respond.Confront.Reply.Disagree",
    "React.Respond.Confront.Reply.Disawow",
    "React.Respond.Support.Develop.Elaborate",
    "React.Respond.Support.Develop.Enhance",
    "React.Respond.Support.Develop.Extend",
    "React.Respond.Support.Engage",
    "React.Respond.Support.Register",
    "React.Respond.Support.Reply.Acknowledge",
    "React.Respond.Support.Reply.Affirm",
    "React.Respond.Support.Reply.Agree",
    "React.Respond.Support.Response.Resolve",
    "Sustain.Continue.Monitor",
    "Sustain.Continue.Prolong.Elaborate",
    "Sustain.Continue.Prolong.Enhance",
    "Sustain.Continue.Prolong.Extend",
]


def check_sfc(full_labels, label, labels, probabilities, pattern=""):
    new_label_idx = int(labels.index(label)) + 1
    for i in range(len(full_labels)):
        if pattern in full_labels[i]:
            if pattern == "Track.":
                if "Probe" not in full_labels[i]:
                    if full_labels[i] not in labels:
                        labels.insert(new_label_idx, full_labels[i])
                        probabilities.insert(new_label_idx, probabilities[labels.index(label)])
            else:
                if full_labels[i] not in labels:
                    labels.insert(new_label_idx, full_labels[i])
                    probabilities.insert(new_label_idx, probabilities[labels.index(label)])


def predict(label_name):
    probabilities = []
    labels = []
    try:
        class_id = class_dict[label_name]
    except KeyError:
        return [{}]
    sorted_classes = sorted(enumerate(counters[class_id]), reverse=True, key=lambda x: x[1])[:5]
    for label, probability in sorted_classes:
        probabilities.append(probability)
        labels.append(label_to_name[label])
        for sf in labels:
            if "Prolong" in sf:
                check_sfc(full_labels, sf, labels, probabilities, "Sustain.Continue.Prolong")
            if "Track" in sf:
                check_sfc(full_labels, sf, labels, probabilities, "Track.")
            if "Develop" in sf:
                check_sfc(full_labels, sf, labels, probabilities, "Develop")
            if "Reply" in sf:
                check_sfc(full_labels, sf, labels, probabilities, "Reply")
    return [{"prediction": label, "confidence": probability} for label, probability in zip(labels, probabilities)]


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
        responses = [predict(speech_function.strip(".")) for speech_function in payload]
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
    return [responses]


@app.post("/annotation")
async def annotation(payload: List[str]):
    st_time = time.time()
    responses = await handler(payload)
    total_time = time.time() - st_time
    logger.info(f"speech_function_predictor batch exec time: {total_time:.3f}s")
    return [{"batch": responses}]
