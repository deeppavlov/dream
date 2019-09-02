import os
import logging
from typing import List
import random

from fastapi import FastAPI, Body
from pydantic import BaseModel
import torch

from pytorch_pretrained_bert import OpenAIGPTLMHeadModel, OpenAIGPTTokenizer
from utils import download_pretrained_model
from interact import sample_sequence


SEED = 31415
# DEVICE = "cuda"
DEVICE = "cpu"
MAX_HISTORY = 2
MAX_LENGTH = 20
MIN_LENGTH = 1
MODEL = "gpt"
MODEL_PATH = os.getenv("MODEL_PATH", "./models")
TEMPERATURE = 0.7
TOP_K = 0
TOP_P = 0.9
NO_SAMPLE = True

args = lambda: None
args.max_length = MAX_LENGTH
args.device = DEVICE
args.model = MODEL
args.temperature = TEMPERATURE
args.top_k = TOP_K
args.top_p = TOP_P
args.no_sample = NO_SAMPLE
args.min_length = MIN_LENGTH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler("../logs/{}.log".format(date)),
    ],
)


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

tokenizer_class = OpenAIGPTTokenizer
tokenizer = tokenizer_class.from_pretrained(MODEL_PATH)
model_class = OpenAIGPTLMHeadModel
model = model_class.from_pretrained(MODEL_PATH)

model.to(DEVICE)
model.eval()


def inference(personality, utterances_histories):
    personality = [tokenizer.encode(ut) for ut in personality]
    history = [tokenizer.encode(ut) for ut in utterances_histories]
    history = history[-(2 * MAX_HISTORY + 1) :]
    with torch.no_grad():
        out_ids, out_probs = sample_sequence(personality, history, tokenizer, model, args)
    if out_probs:
        return tokenizer.decode(out_ids, skip_special_tokens=True), float(sum(out_probs) / len(out_probs))
    else:
        return "", 0.0


@app.post("/transfertransfo/")
def transfer_transfo_chitchat_model(placeholders: Input_placeholders):
    response = [
        inference(pers, hist) for pers, hist in zip(placeholders.personality, placeholders.utterances_histories)
    ]
    return response
