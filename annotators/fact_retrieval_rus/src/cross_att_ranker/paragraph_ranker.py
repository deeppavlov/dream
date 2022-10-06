from logging import getLogger

import torch
import torch.nn as nn

from transformers import AutoConfig, AutoTokenizer, AutoModel
from deeppavlov.core.common.registry import register

log = getLogger(__name__)


@register("paragraph_ranking_infer")
class ParagraphRankerInfer:
    def __init__(
        self,
        pretrained_bert: str = None,
        encoder_save_path: str = None,
        linear_save_path: str = None,
        return_probas: bool = True,
        batch_size: int = 60,
        **kwargs,
    ):
        self.pretrained_bert = pretrained_bert
        self.encoder_save_path = encoder_save_path
        self.linear_save_path = linear_save_path
        self.return_probas = return_probas
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load()
        tokenizer = AutoTokenizer.from_pretrained(pretrained_bert)
        self.encoder.resize_token_embeddings(len(tokenizer) + 1)
        self.batch_size = batch_size

    def load(self) -> None:
        if self.pretrained_bert:
            log.info(f"From pretrained {self.pretrained_bert}.")
            self.config = AutoConfig.from_pretrained(self.pretrained_bert, output_hidden_states=True)
            self.encoder = AutoModel.from_pretrained(self.pretrained_bert, config=self.config)
            self.fc = nn.Linear(self.config.hidden_size, 1)
        self.encoder.to(self.device)
        self.fc.to(self.device)

    def __call__(self, input_features_batch):
        scores_batch = []
        for input_features in input_features_batch:
            input_ids = input_features["input_ids"]
            attention_mask = input_features["attention_mask"]
            num_batches = len(input_ids) // self.batch_size + int(len(input_ids) % self.batch_size > 0)
            scores_list = []
            for i in range(num_batches):
                cur_input_ids = input_ids[i * self.batch_size : (i + 1) * self.batch_size]
                cur_attention_mask = attention_mask[i * self.batch_size : (i + 1) * self.batch_size]
                cur_input_ids = torch.LongTensor(cur_input_ids).to(self.device)
                cur_attention_mask = torch.LongTensor(cur_attention_mask).to(self.device)
                with torch.no_grad():
                    encoder_output = self.encoder(input_ids=cur_input_ids, attention_mask=cur_attention_mask)
                    cls_emb = encoder_output.last_hidden_state[:, :1, :].squeeze(1)
                    scores = self.fc(cls_emb)
                scores = scores.cpu().numpy().tolist()
                scores_list += scores
            scores_list = [elem[0] for elem in scores_list]
            scores_batch.append(scores_list)
        return scores_batch
