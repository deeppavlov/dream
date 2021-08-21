import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/bert-base-cased-conversational")
model = AutoModel.from_pretrained("DeepPavlov/bert-base-cased-conversational")


def get_embedding(text: str):
    with torch.no_grad():
        input_ph = tokenizer(
            str(text).replace("?uh", ""), padding=True, truncation=True, max_length=30, return_tensors="pt"
        )
        output_ph = model(**input_ph)
        return output_ph.last_hidden_state.mean(dim=1).cpu().numpy()


def get_features(bot_utt: str, human_utt: str):
    return np.concatenate([get_embedding(human_utt), get_embedding(bot_utt)], axis=1)
