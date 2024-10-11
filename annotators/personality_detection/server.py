import logging
import os
import numpy as np
import torch
import sentry_sdk
import random

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import Any, List
from fastapi import FastAPI, Body
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware


sentry_sdk.init(os.getenv("SENTRY_DSN"))


torch.manual_seed(42)
random.seed(42)
np.random.seed(42)

tokenizer = AutoTokenizer.from_pretrained('tae898/emoberta-base')
max_len = 128
traits = ['extraversion', 'neuroticism', 'agreeableness', 'conscientiousness', 'openness']
models = {}

for trait in traits:
    path = f'/data/{trait}_tae898_emoberta-base_seed-42.pt'
    model = AutoModelForSequenceClassification.from_pretrained('tae898/emoberta-base', num_labels=2, ignore_mismatched_sizes=True)
    model.to('cuda')
    model.load_state_dict(torch.load(path, map_location=torch.device('cuda')), strict=False)
    models[trait] = model

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
        # results = {}
        results = {
            'traits': {},
            'traits_proba': {}
            }
        for trait in traits:
            trait_model = models[trait]
            inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=max_len)
            with torch.no_grad():
                input_ids = inputs['input_ids'].to('cuda')
                attn_mask = inputs['attention_mask'].to('cuda')
                output = trait_model(input_ids=input_ids, attention_mask=attn_mask)
                predictions = torch.softmax(output['logits'], dim=1)
                results['traits'][trait.upper()] = torch.argmax(predictions, dim=1).item()
                results['traits_proba'][trait.upper()] = list(np.array(predictions.cpu()[0]))
        return results
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
