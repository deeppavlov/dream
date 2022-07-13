import torch
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