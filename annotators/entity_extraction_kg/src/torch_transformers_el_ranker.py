# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from logging import getLogger
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union, Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoConfig, AutoTokenizer, AutoModel

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.errors import ConfigError
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.torch_model import TorchModel
from src.torch_transformers_preprocessor import TorchTransformersEntityRankerPreprocessor

log = getLogger(__name__)


class TextEncoder(nn.Module):
    def __init__(self, pretrained_bert: str = None,
                 bert_tokenizer_config_file: str = None,
                 bert_config_file: str = None,
                 resize: bool = False,
                 device: str = "gpu"
                 ):
        super().__init__()
        self.pretrained_bert = pretrained_bert
        self.bert_config_file = bert_config_file
        self.encoder, self.config, self.bert_config = None, None, None
        self.device = device
        self.load()
        self.resize = resize
        self.tokenizer = AutoTokenizer.from_pretrained(self.pretrained_bert)
        if self.resize:
            self.encoder.resize_token_embeddings(len(self.tokenizer) + 1)
        
    def forward(self,
                input_ids: Tensor,
                attention_mask: Tensor,
                entity_tokens_pos: List[int] = None
    ) -> Union[Tuple[Any, Tensor], Tuple[Tensor]]:

        if self.resize:
            q_outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            q_hidden_states = q_outputs.last_hidden_state
            
            entity_emb = []
            for i in range(len(entity_tokens_pos)):
                pos = entity_tokens_pos[i]
                entity_emb.append(q_hidden_states[i, pos])
            
            entity_emb = torch.stack(entity_emb, dim=0)
            return entity_emb
        else:
            c_outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            c_cls_emb = c_outputs.last_hidden_state[:,:1,:].squeeze(1)
            return c_cls_emb
            
    def load(self) -> None:
        if self.pretrained_bert:
            log.info(f"From pretrained {self.pretrained_bert}.")
            self.config = AutoConfig.from_pretrained(
                self.pretrained_bert, output_hidden_states=True
            )
            self.encoder = AutoModel.from_pretrained(self.pretrained_bert, config=self.config)

        elif self.bert_config_file and Path(self.bert_config_file).is_file():
            self.config = AutoConfig.from_json_file(str(expand_path(self.bert_config_file)))
            self.encoder = AutoModel.from_config(config=self.bert_config)
        else:
            raise ConfigError("No pre-trained BERT model is given.")
        self.encoder.to(self.device)


class BilinearRanking(nn.Module):
    """Class for calculation of bilinear form of two vectors
    Args:
        n_classes: number of classes for classification
        emb_size: entity embedding size
        block_size: size of block in bilinear layer
    """

    def __init__(self, n_classes: int = 2, emb_size: int = 512, block_size: int = 8):
        super().__init__()
        self.n_classes = n_classes
        self.emb_size = emb_size
        self.block_size = block_size
        self.bilinear = nn.Linear(self.emb_size * self.block_size, self.n_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, text1: Tensor, text2: Tensor):
        b1 = text1.view(-1, self.emb_size // self.block_size, self.block_size)
        b2 = text2.view(-1, self.emb_size // self.block_size, self.block_size)
        bl = (b1.unsqueeze(3) * b2.unsqueeze(2)).view(-1, self.emb_size * self.block_size)
        logits = self.bilinear(bl)
        softmax_logits = self.softmax(logits)
        log_softmax = F.log_softmax(logits, dim=-1)
        return softmax_logits, log_softmax


@register('torch_transformers_entity_ranker_infer')
class TorchTransformersEntityRankerInfer:
    """Class for infering of model for ranking of entities from a knowledge base by context and description
    Args:
        pretrained_bert: pretrained Bert checkpoint path or key title (e.g. "bert-base-uncased")
        encoder_weights_path: path to save the encoder checkpoint
        bilinear_weights_path: path to save bilinear layer checkpoint
        spaecial_token_id: id of special token
        do_lower_case: whether to lower case the text
        batch_size: batch size when model infering
        emb_size: entity embedding size
        block_size: size of block in bilinear layer
        device: `cpu` or `gpu` device to use
    """

    def __init__(self, pretrained_bert,
                 text_encoder_weights_path,
                 descr_encoder_weights_path,
                 bilinear_weights_path,
                 special_token_id: int,
                 do_lower_case: bool = True,
                 batch_size: int = 5,
                 emb_size: int = 512,
                 block_size: int = 8,
                 device: str = "gpu", **kwargs):
        self.device = torch.device("cuda" if torch.cuda.is_available() and device == "gpu" else "cpu")
        self.pretrained_bert = str(expand_path(pretrained_bert))
        self.preprocessor = TorchTransformersEntityRankerPreprocessor(vocab_file=self.pretrained_bert,
                                                                      do_lower_case=do_lower_case,
                                                                      special_tokens=["[ent]"])
        self.encoder, self.config = None, None
        self.config = AutoConfig.from_pretrained(self.pretrained_bert, output_hidden_states=True)
        self.emb_size = emb_size
        self.block_size = block_size
        self.text_encoder = TextEncoder(pretrained_bert=self.pretrained_bert, resize=True, device=self.device)
        self.descr_encoder = TextEncoder(pretrained_bert=self.pretrained_bert, device=self.device)
        self.text_encoder_weights_path = str(expand_path(text_encoder_weights_path))
        self.descr_encoder_weights_path = str(expand_path(descr_encoder_weights_path))
        self.bilinear_weights_path = str(expand_path(bilinear_weights_path))
        text_encoder_checkpoint = torch.load(self.text_encoder_weights_path, map_location=self.device)
        self.text_encoder.load_state_dict(text_encoder_checkpoint["model_state_dict"])
        self.text_encoder.to(self.device)
        
        descr_encoder_checkpoint = torch.load(self.descr_encoder_weights_path, map_location=self.device)
        self.descr_encoder.load_state_dict(descr_encoder_checkpoint["model_state_dict"])
        self.descr_encoder.to(self.device)
        
        self.bilinear_ranking = BilinearRanking(emb_size=self.emb_size, block_size=self.block_size)
        bilinear_checkpoint = torch.load(self.bilinear_weights_path, map_location=self.device)
        self.bilinear_ranking.load_state_dict(bilinear_checkpoint["model_state_dict"])
        self.bilinear_ranking.to(self.device)
        self.special_token_id = special_token_id
        self.batch_size = batch_size

    def __call__(self, contexts_batch: List[str],
                 candidate_entities_batch: List[List[str]],
                 candidate_entities_descr_batch: List[List[str]]):
        entity_emb_batch = []

        num_batches = len(contexts_batch) // self.batch_size + int(len(contexts_batch) % self.batch_size > 0)
        for ii in range(num_batches):
            contexts_list = contexts_batch[ii * self.batch_size:(ii + 1) * self.batch_size]
            context_features = self.preprocessor(contexts_list)
            context_input_ids = context_features["input_ids"].to(self.device)
            context_attention_mask = context_features["attention_mask"].to(self.device)
            special_tokens_pos = []
            for input_ids_list in context_input_ids:
                found_n = -1
                for n, input_id in enumerate(input_ids_list):
                    if input_id == self.special_token_id:
                        found_n = n
                        break
                if found_n == -1:
                    found_n = 0
                special_tokens_pos.append(found_n)
            cur_entity_emb_batch = self.text_encoder(input_ids=context_input_ids,
                                                     attention_mask=context_attention_mask,
                                                     entity_tokens_pos=special_tokens_pos)

            entity_emb_batch += cur_entity_emb_batch.detach().cpu().numpy().tolist()

        scores_batch = []
        for entity_emb, candidate_entities_list, candidate_entities_descr_list in \
                zip(entity_emb_batch, candidate_entities_batch, candidate_entities_descr_batch):
            if candidate_entities_list:
                entity_emb = [entity_emb for _ in candidate_entities_list]
                entity_emb = torch.Tensor(entity_emb).to(self.device)
                descr_features = self.preprocessor(candidate_entities_descr_list)
                descr_input_ids = descr_features["input_ids"].to(self.device)
                descr_attention_mask = descr_features["attention_mask"].to(self.device)
                candidate_entities_emb = self.descr_encoder(input_ids=descr_input_ids,
                                                      attention_mask=descr_attention_mask)
                scores_list, _ = self.bilinear_ranking(entity_emb, candidate_entities_emb)
                scores_list = scores_list.detach().cpu().numpy()
                scores_list = [score[1] for score in scores_list]
                scores_batch.append(scores_list)
            else:
                scores_batch.append([])

        return scores_batch
