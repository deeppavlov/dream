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


N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))

tokenizer = AutoTokenizer.from_pretrained("dim/dialogpt-medium-persona-chat")
model = AutoModelForCausalLM.from_pretrained("dim/dialogpt-medium-persona-chat")
sentence_model = SentenceTransformer('nli-distilroberta-base-v2')
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
persona = open("./persona_sentences.txt").read()
model = model.to(device)

persona_sentences = persona.split("\n")
persona_sentences = [item for item in persona_sentences if len(item) > 0]
sentence_ranker = SentenceRanker(
    persona_sentences=persona_sentences,
    sentence_model=sentence_model
)

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

    user_input = context[-1][-1]
    # get more relevant persona pieces
    persona, max_prob = sentence_ranker.rank_sentences([user_input], k=2)
    persona = " ".join(persona)

    # print(f"Persona: {persona}")
    # print(f"Dreaming: {True if max_prob < threshhold else False} - {max_prob} ")
    persona = f"{SPECIAL_TOKENS['<persona>']}{persona}{SPECIAL_TOKENS['</persona>']}"
    print(persona)
    persona_ids = tokenizer.encode(persona, return_tensors='pt')
    persona_ids = persona_ids.to(device)
    
    print(f"User: {user_input}")

    # user_input = f"{SPECIAL_TOKENS['<sp_1>']}{user_input}{SPECIAL_TOKENS['</sp_1>']}{SPECIAL_TOKENS['<sp_2>']}"

    new_user_input_ids = tokenizer.encode(user_input, return_tensors='pt')
    # new_user_input_ids = new_user_input_ids.to(device)

    history_chat = "".join([f"<sp_{i%2+1}>{item}</sp_{i%2+1}>" for i, item in enumerate(context[0][-3:])])
    history_chat += "<sp_2>"
    print(history_chat)

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

    # model_response = model_response.to(device)
    model_response_list = list(model_response[0])

    end_speaker_index = last_index(model_response_list, VOCAB_TOKENS['</sp_2>'])
    model_response = model_response[:, :end_speaker_index+1]

    chat_history_ids = model_response
    bot_response_decode = tokenizer.decode(chat_history_ids[0][len(bot_input_ids[0])-1:], skip_special_tokens=True) 
    
    print(f"Bot: {bot_response_decode}")
    return bot_response_decode

def test_respond():
    contexts = [[
        "Hello. How is you dad?", 
        "i am good. i am just watching a movie.", 
        "Do you like puzzles?", 
        "i love puzzles! i am obsessed with them.",
        "I hate dogs!"
    ]]
    responses = generate_response(model=model, tokenizer=tokenizer, context=contexts)
    print("Success")


if __name__ == "__main__":
    test_respond()
