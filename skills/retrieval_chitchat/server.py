import os
from typing import List
import logging
import pickle
import random
import time

import numpy as np
from fastapi import FastAPI, Body
from pydantic import BaseModel
import torch
import sentry_sdk
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize


SEED = 31415
DEVICE = "cpu"
MODEL_PATH = os.getenv("MODEL_PATH", "./models")
DATABASE_PATH = os.getenv("DATABASE_PATH")
CONFIDENCE_PATH = os.getenv("CONFIDENCE_PATH")
EMBEDDING_SPLIT_BY = 27

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)

logger = logging.getLogger(__name__)

model = SentenceTransformer(MODEL_PATH)
database = pickle.load(open(DATABASE_PATH, "rb"))
confidence = np.load(CONFIDENCE_PATH)
embeddings = normalize(np.array([el["embedding"] for el in database]))
splitted_embeddings = np.split(embeddings, EMBEDDING_SPLIT_BY)


class Input_placeholders(BaseModel):
    personality: List[List[str]] = Body(
        ...,
        example=[
            [
                "i prefer vinyl records to any other music recording format.",
                "i fix airplanes for a living.",
                "drive junk cars that no one else wants.",
                "i think if i work hard enough i can fix the world.",
                "i am never still.",
            ]
        ],
    )
    utterances_histories: List[List[str]] = Body(..., example=[["Hello", "Hi", "How are you?"]])


app = FastAPI()

random.seed(SEED)
torch.random.manual_seed(SEED)
torch.cuda.manual_seed(SEED)

model.to(DEVICE)
model.eval()

sep_token = " [SEP] "
top_k = 10


def inference(personality, utterance):
    personality_input = " ".join(personality)
    utterance_input = utterance[-1]
    model_input = [utterance_input + sep_token + personality_input]
    with torch.no_grad():
        encoded_query = model.encode(model_input)
    # to split embeddings tensor for OOM avoid
    encoded_query = normalize(encoded_query)[0]
    cosine_similarity = []
    for embedding_slice in splitted_embeddings:
        cosine_similarity.append(embedding_slice.dot(encoded_query))
    cosine_similarity = np.concatenate(cosine_similarity)

    top_k_idx = np.flip(np.argsort(cosine_similarity, -1), -1)[:top_k]
    top_k_confidence = [len([i for i in confidence if i < cosine_similarity[idx]]) for idx in top_k_idx]
    top_k_confidence = np.array(top_k_confidence) / len(confidence)
    top_k_responses = [(database[idx]["response"], conf) for idx, conf in zip(top_k_idx, top_k_confidence)]
    return top_k_responses[0]


@app.post("/retrieval_chitchat/")
def retrieval_chitchat_model(placeholders: Input_placeholders):
    st_time = time.time()
    response = [
        inference(pers, hist) for pers, hist in zip(placeholders.personality, placeholders.utterances_histories)
    ]
    total_time = time.time() - st_time
    logger.info(f"retrieval_chitchat exec time: {total_time:.3f}s")
    return response
