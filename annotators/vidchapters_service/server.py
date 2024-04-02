import logging
import os
import pickle
import re
from typing import Any, List

import numpy as np
import sentry_sdk
from fastapi import FastAPI, Body
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

sentry_sdk.init(os.getenv("SENTRY_DSN"))

cEXT = pickle.load(open("/data/models/cEXT.p", "rb"))
cNEU = pickle.load(open("/data/models/cNEU.p", "rb"))
cAGR = pickle.load(open("/data/models/cAGR.p", "rb"))
cCON = pickle.load(open("/data/models/cCON.p", "rb"))
cOPN = pickle.load(open("/data/models/cOPN.p", "rb"))
vectorizer_31 = pickle.load(open("/data/models/vectorizer_31.p", "rb"))
vectorizer_30 = pickle.load(open("/data/models/vectorizer_30.p", "rb"))


logger = logging.getLogger(__name__)


def jsonify_data(data: Any) -> Any:
    """Replaces JSON-non-serializable objects with JSON-serializable.

    Function replaces numpy arrays and numbers with python lists and numbers, tuples is replaces with lists. All other
    object types remain the same.

    Args:
        data: Object to make JSON-serializable.

    Returns:
        Modified input data.

    """
    if isinstance(data, (list, tuple)):
        result = [jsonify_data(item) for item in data]
    elif isinstance(data, dict):
        result = {}
        for key in data.keys():
            result[key] = jsonify_data(data[key])
    elif isinstance(data, np.ndarray):
        result = data.tolist()
    elif isinstance(data, np.integer):
        result = int(data)
    elif isinstance(data, np.floating):
        result = float(data)
    elif callable(getattr(data, "to_serializable_dict", None)):
        result = data.to_serializable_dict()
    else:
        result = data
    return result


def predict_personality(text):
    try:
        scentences = re.split("(?<=[.!?]) +", text)
        text_vector_31 = vectorizer_31.transform(scentences)
        text_vector_30 = vectorizer_30.transform(scentences)
        EXT = cEXT.predict(text_vector_31)
        NEU = cNEU.predict(text_vector_30)
        AGR = cAGR.predict(text_vector_31)
        CON = cCON.predict(text_vector_31)
        OPN = cOPN.predict(text_vector_31)
        return {"EXT": EXT[0], "NEU": NEU[0], "AGR": AGR[0], "CON": CON[0], "OPN": OPN[0]}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise e


app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


class PersonalityPayload(BaseModel):
    personality: List[str] = Body(...)


@app.post("/model")
def infer(payload: PersonalityPayload):
    logger.info(f"Personality Detection: {payload}")
    personality = [predict_personality(p) for p in payload.personality]
    return jsonify_data(personality)
