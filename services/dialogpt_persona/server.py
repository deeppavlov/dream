from sentence_transformers import SentenceTransformer
import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer
# from sentence_ranker import SentenceRanker
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
		max_prob = cos_sim_ranks[top_indices][0]
		top_indices = list(top_indices[:k].cpu().numpy())
		similar_sentences = [self.persona_sentences[idx] for idx in top_indices]
		self.ranked_sentences[key] = similar_sentences 
		return similar_sentences, max_prob
	
	def cos_sim(self, a, b):
		a_norm = torch.nn.functional.normalize(a, p=2, dim=1)
		b_norm = torch.nn.functional.normalize(b, p=2, dim=1)
		return torch.sum(a_norm * b_norm, dim=1)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
# logging.info(f'PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}')
DEFAULT_CONFIDENCE = 10
N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3

try:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    sentence_model = SentenceTransformer('nli-distilroberta-base-v2')
    persona = open("./persona_sentences.txt").read()
    model = model.to(device)

    persona_sentences = persona.split("\n")
    persona_sentences = [item for item in persona_sentences if len(item) > 0]
    sentence_ranker = SentenceRanker(
	    persona_sentences=persona_sentences,
	    sentence_model=sentence_model
    )

    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("dialogpt_persona is set to run on cuda")

    logger.info("dialogpt_persona is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("INFO")

def last_index(array, elem):
    return len(array) - 1 - array[::-1].index(elem)

def generate_response(context, model, tokenizer):
    SPECIAL_TOKENS = { 
        "<sp_1>": "<sp_1>",
        "</sp_1>": "</sp_1>",
        "<sp_2>": "<sp_2>",
        "</sp_2>": "</sp_2>",
        "<persona>": "<persona>",
        "</persona>": "</persona>",
    }
    VOCAB_TOKENS = tokenizer.get_added_vocab()
    threshhold = 0.3
    context = context[0]
    user_input = context[-1]

    persona, max_prob = sentence_ranker.rank_sentences([user_input], k=2)
    persona = " ".join(persona)
    persona = f"{SPECIAL_TOKENS['<persona>']}{persona}{SPECIAL_TOKENS['</persona>']}"

    persona_ids = tokenizer.encode(persona, return_tensors='pt')
    persona_ids = persona_ids.to(device)
    
    print(f"User: {user_input}")

    
    history_chat = "".join(list(reversed([f"<sp_{(i)%2+1}>{item}</sp_{(i)%2+1}>" for i, item in enumerate(reversed(context[-5:]))])))
    history_chat += "<sp_2>"
    logger.info(history_chat)

    history_ids = tokenizer.encode(history_chat, return_tensors='pt')
    history_ids = history_ids.to(device)
    
    bot_input_ids = torch.cat([persona_ids, history_ids], dim=-1)
    if max_prob > threshhold:
        model_response = model.generate(
            bot_input_ids, 
            max_length=500,
            pad_token_id=tokenizer.eos_token_id,  
            do_sample=True, 
            num_beams=2, 
            temperature = 0.95,
            top_k=100, 
            top_p=0.95,
        )
    else:
        model_response = model.generate(
            bot_input_ids, 
            max_length=500,
            pad_token_id=tokenizer.eos_token_id,  
            do_sample=True, 
            # num_beams=3, 
            temperature = 0.95,
            top_k=100, 
            top_p=0.95,
        )

    model_response = model_response.to(device)
    model_response_list = list(model_response[0])

    end_speaker_index = last_index(model_response_list, VOCAB_TOKENS['</sp_2>'])
    model_response = model_response[:, :end_speaker_index+1]

    chat_history_ids = model_response
    bot_response_decode = tokenizer.decode(chat_history_ids[0][len(bot_input_ids[0])-1:], skip_special_tokens=True) 
    
    print(f"Bot: {bot_response_decode}")
    return bot_response_decode


@app.route("/respond", methods=["POST"])
def respond():
    contexts = request.json.get("utterances_histories", [])
    # print(contexts)
    try:
        responses = generate_response(model=model, tokenizer=tokenizer, context=contexts)

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
    
    responses = [[responses]] 
    confidences = [[0.95]] 

    return jsonify(list(zip(responses, confidences)))
