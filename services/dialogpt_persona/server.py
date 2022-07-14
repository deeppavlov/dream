import logging
import time
import os
from typing import List

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
DEFAULT_CONFIDENCE = 0.95
N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3
MAX_PERSONA_SENTENCES = 3

try:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)

    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("dialogpt_persona is set to run on cuda")

    logger.info("dialogpt_persona is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
# logging.getLogger("werkzeug").setLevel("INFO")

def last_index(array, elem):
    return len(array) - 1 - array[::-1].index(elem)

def generate_response(
        persona: List[List[str], float]=None,  
        model: AutoModelForCausalLM =None, 
        tokenizer: AutoTokenizer=None, 
        utterances_histories: List[List[str]]=None
    ) -> str:
    """генерирует следующую реплику бота на основе короткой персоны состоящей из нескольких предложений.

    Args:
        persona (List[List[str], float]): Топ предложений похожих на последнюю реплику. Defaults to None.
        model (AutoModelForCausalLM): gpt модель. Defaults to None.
        tokenizer (AutoTokenizer): gpt токенизатор. Defaults to None.
        utterances_histories (List[List[str]]): история диалога. Defaults to None.

    Returns:
        str: следующая реплика
    """
    
    SPECIAL_TOKENS = { 
        "<sp_1>": "<sp_1>",
        "</sp_1>": "</sp_1>",
        "<sp_2>": "<sp_2>",
        "</sp_2>": "</sp_2>",
        "<persona>": "<persona>",
        "</persona>": "</persona>",
    }
    VOCAB_TOKENS = tokenizer.get_added_vocab()
    threshhold = 0.2
    
    max_likelihood_sentences, max_sentence_similarity = persona
    max_likelihood_sentences = max_likelihood_sentences[:MAX_PERSONA_SENTENCES]
    max_likelihood_sentences = " ".join(max_likelihood_sentences)
    max_likelihood_sentences = f"{SPECIAL_TOKENS['<persona>']}{max_likelihood_sentences}{SPECIAL_TOKENS['</persona>']}"

    persona_ids = tokenizer.encode(max_likelihood_sentences, return_tensors='pt')
    persona_ids = persona_ids.to(device)
    
    utterances_histories = utterances_histories[0]
    history_chat = "".join(list(reversed([f"<sp_{(i)%2+1}>{item}</sp_{(i)%2+1}>" for i, item in enumerate(reversed(utterances_histories[-5:]))])))
    history_chat += "<sp_2>"

    history_ids = tokenizer.encode(history_chat, return_tensors='pt')
    history_ids = history_ids.to(device)
    
    bot_input_ids = torch.cat([persona_ids, history_ids], dim=-1)
    if max_sentence_similarity > threshhold:
        model_response = model.generate(
            bot_input_ids, 
            max_length=250,
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
            max_length=250,
            pad_token_id=tokenizer.eos_token_id,  
            do_sample=True, 
            temperature = 0.95,
            top_k=100, 
            top_p=0.95,
        )


    model_response = model_response.to(device)
    model_response_list = list(model_response[0])

    end_speaker_index = model_response_list.index(VOCAB_TOKENS['</sp_2>'])
    model_response = model_response[:, :end_speaker_index+1]

    chat_history_ids = model_response
    bot_response_decode = tokenizer.decode(chat_history_ids[0][len(bot_input_ids[0])-1:], skip_special_tokens=True) 
    
    return bot_response_decode


@app.route("/respond", methods=["POST"])
def respond():
    
    persona = request.json['dialogs'][0]['human_utterances'][-1]['annotations']['sentence_ranker']
    utterances_histories = request.json['utterances_histories']
    try:
        response = generate_response(
            model=model, 
            tokenizer=tokenizer, 
            persona=persona, 
            utterances_histories=utterances_histories
        )
        
        response = [[response]] 
        confidences = [[DEFAULT_CONFIDENCE]] 

        return jsonify(list(zip(response, confidences)))

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc) 
