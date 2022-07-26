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
from common.utils import get_intents

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("werkzeug").setLevel("INFO")

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
DEFAULT_CONFIDENCE = 1.0


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
logging.getLogger("werkzeug").setLevel("INFO")
MAX_PERSONA_SENTENCES = 3

def generate_response(
        persona=None,  
        model=None, 
        tokenizer=None, 
        utterances_histories=None
    ):
    """generates the next replica of the bot based on a short persona consisting of several sentences.

    Args:
        persona (List[List[str], float]): Top sentences similar to the last replica. Defaults to None.
        model (AutoModelForCausalLM): gpt model. Defaults to None.
        tokenizer (AutoTokenizer): gpt tokenizer. Defaults to None.
        utterances_histories (List[List[str]]): dialog history. Defaults to None.

    Returns:
        str: next utterance
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
    history_chat = "".join(list(reversed([f"<sp_{(i)%2+1}>{item}</sp_{(i)%2+1}>" for i, item in enumerate(reversed(utterances_histories[-1:]))])))
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
            temperature=0.95,
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
    try:
        start_time = time.time()
        responses = [] 
        confidences = []
        for utt_pos in range(len(request.json['persona'])):
            persona = request.json['persona'][utt_pos]
            utterances_histories = request.json['utterances_histories']

            intents = request.json['intents'][utt_pos]
            if "open_question_personal" in get_intents(intents):
                logger.info("open_question_personal")
                DEFAULT_CONFIDENCE = 1.0
            else:
                logger.info("NOT open_question_personal")
                DEFAULT_CONFIDENCE = 0.95
            
            response = generate_response(
                model=model, 
                tokenizer=tokenizer, 
                persona=persona, 
                utterances_histories=utterances_histories
            )

            responses.append([response]) 
            confidences.append([DEFAULT_CONFIDENCE])

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc) 

    total_time = time.time() - start_time
    logger.info(f"dialog_persona exec time: {total_time:.3f}s")
    
    return jsonify(list(zip(responses, confidences)))