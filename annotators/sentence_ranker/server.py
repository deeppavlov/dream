import logging
import os
import time

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sentry_sdk.integrations.flask import FlaskIntegration

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


class SentenceRanker:
    def __init__(self, 
        persona_sentences=None, 
        sentence_model=None
    ):
        """ranks a person's sentences based on context

        Args:
            persona_sentences (List[str]): a list of sentences constituting a complete person. Defaults to None.
            sentence_model (SentenceTransformer): model for translating a sentence into a vector. Defaults to None.
        """
        self.persona_sentences = persona_sentences
        self.sentence_model = sentence_model
        self.sentence_embeddings = self.sentence_model.encode(
            persona_sentences, 
            convert_to_tensor=True
        )
        # for caching similar queries
        self.ranked_sentences = {}
    
    def rank_sentences(self, query, k):
        """returns top k sentences that are similar to query

        Args:
            query (str): sentence on the basis of which we are looking for similar
            k (int): the number of sentences returned. Defaults to 5.

        Returns:
            List[List[str], float]: ranked sentences and maximum cosine distance among all 
        """
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
        self.ranked_sentences[key] = similar_sentences, max_similarity 
        return [similar_sentences, max_similarity]
    
    def cos_sim(self, a, b):
        """returns the cosine distance
        
        K - number of sentences to compare
        N - dimension of the returned vector
        Args:
            a (torch.FloatTensor): shape (1, N)
            b (torch.FloatTensor): shape (K, N)

        Returns:
            torch.FloatTensor: shape (1, K) tensor with cosine distances
        """
        a_norm = torch.nn.functional.normalize(a, p=2, dim=1)
        b_norm = torch.nn.functional.normalize(b, p=2, dim=1)
        return torch.sum(a_norm * b_norm, dim=1)


PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
TOP_SIMILAR_SENTENCES = int(os.environ.get("TOP_SIMILAR_SENTENCES", 5))

try:
    sentence_model = SentenceTransformer(PRETRAINED_MODEL_NAME_OR_PATH)
    
    persona = open("../../common/persona_sentences.txt").read()
    persona_sentences = persona.split("\n")
    persona_sentences = [item.strip() for item in persona_sentences if len(item) > 0]
    
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
        start_time = time.time()
        dialogs = request.json.get("dialogs", [])
        process_result = []
        for last_utterance in dialogs:
            # take the last replica, then take the result of the sentseg annotator from it
            last_utterance = last_utterance["human_utterances"][-1]["annotations"]['sentseg']['punct_sent']
            max_likelihood_sentences, max_sentence_similarity = sentence_ranker.rank_sentences(
                [last_utterance], 
                k=TOP_SIMILAR_SENTENCES
            )
            
            process_result.append([
                max_likelihood_sentences, 
                max_sentence_similarity
            ])

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)

    total_time = time.time() - start_time
    logger.info(f"sentence_ranker exec time: {total_time:.3f}s")
    return jsonify(
        process_result
    )
