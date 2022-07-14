from sentence_transformers import SentenceTransformer
import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

class SentenceRanker:
    def __init__(self, persona_sentences=None, sentence_model=None):
        self.persona_sentences = persona_sentences
        self.sentence_model = sentence_model
        self.sentence_embeddings = self.sentence_model.encode(
            persona_sentences, 
            convert_to_tensor=True
        )
        self.ranked_sentences = {}
    
    def rank_sentences(self, query, k=5):
        key = f"{query}_{k}"
        if self.ranked_sentences.get(key, False):
            return self.ranked_sentences[key]
        user_sentence_embeddings = self.sentence_model.encode(query, convert_to_tensor=True)

        cos_sim_ranks = self.cos_sim(
            user_sentence_embeddings,
            self.sentence_embeddings
        )
        
        top_indices = torch.argsort(cos_sim_ranks, descending=True)
        max_similarity = float(cos_sim_ranks[top_indices][0])
        top_indices = list(top_indices[:k].cpu().numpy())
        similar_sentences = [self.persona_sentences[idx] for idx in top_indices]
        self.ranked_sentences[key] = similar_sentences 
        return similar_sentences, max_similarity
    
    def cos_sim(self, a, b):
        a_norm = torch.nn.functional.normalize(a, p=2, dim=1)
        b_norm = torch.nn.functional.normalize(b, p=2, dim=1)
        return torch.sum(a_norm * b_norm, dim=1)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("werkzeug").setLevel("INFO")
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
# logging.info(f'PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}')
DEFAULT_CONFIDENCE = 10
N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3

try:
    sentence_model = SentenceTransformer(PRETRAINED_MODEL_NAME_OR_PATH)
    
    persona = open("./persona_sentences.txt").read()
    persona_sentences = persona.split("\n")
    persona_sentences = [item for item in persona_sentences if len(item) > 0]
    
    sentence_ranker = SentenceRanker(
        persona_sentences=persona_sentences,
        sentence_model=sentence_model
    )
    logger.info("sentence_ranker is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)

@app.route("/response", methods=["POST"])
def respond():
    try:
        # logger.info(f"AAAAAAAAAAAAAAAAAAA {request.json} ")
        sentences = request.json.get("sentences", [])
        dialogs = request.json.get("dialogs", [])
        logger.info(f"DIALOGS {dialogs}")
        # dialogs = ["human_utterances"][-1]["annotations"]['sentseg']['punct_sent']
        process_result = []
        context_str = dialogs[0]["human_utterances"][-1]["annotations"]['sentseg']['punct_sent']
        logger.info(f"TEST {context_str}")
        max_likelihood_sentences, max_sentence_similarity = sentence_ranker.rank_sentences([context_str], k=5)
        # process_result.append([
        #     max_likelihood_sentences, 
        #     max_sentence_similarity
        # ])
        process_result.append([
            max_likelihood_sentences, 
            max_sentence_similarity
        ])

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
    logger.info(f"RANKER RESULT {process_result}")
    return jsonify(
        process_result
    )
