from pathlib import Path
from logging import getLogger
from typing import Optional, Dict

import torch
import torch.nn as nn
import numpy as np

from deeppavlov.core.commands.utils import expand_path
from transformers import AutoConfig, AutoTokenizer, AutoModel
from deeppavlov.core.common.errors import ConfigError
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.torch_model import TorchModel

log = getLogger(__name__)


@register("torch_transformers_el_tags")
class TorchTransformersElTags(TorchModel):
    def __init__(
        self,
        model_name: str,
        encoder_save_path: str,
        emb_size: int,
        n_tags: int,
        pretrained_bert: str = None,
        bert_config_file: Optional[str] = None,
        criterion: str = "CrossEntropyLoss",
        optimizer: str = "AdamW",
        optimizer_parameters: Dict = {"lr": 5e-5, "weight_decay": 0.01, "eps": 1e-6},
        return_probas: bool = False,
        attention_probs_keep_prob: Optional[float] = None,
        hidden_keep_prob: Optional[float] = None,
        clip_norm: Optional[float] = None,
        threshold: Optional[float] = None,
        **kwargs,
    ):
        self.encoder_save_path = encoder_save_path
        self.emb_size = emb_size
        self.n_tags = n_tags
        self.pretrained_bert = pretrained_bert
        self.bert_config_file = bert_config_file
        self.return_probas = return_probas
        self.attention_probs_keep_prob = attention_probs_keep_prob
        self.hidden_keep_prob = hidden_keep_prob
        self.clip_norm = clip_norm

        super().__init__(
            model_name=model_name,
            optimizer=optimizer,
            criterion=criterion,
            optimizer_parameters=optimizer_parameters,
            return_probas=return_probas,
            **kwargs,
        )

    def train_on_batch(self, input_ids, attention_mask, entity_subw_indices_batch, labels) -> float:

        _input = {"entity_subw_indices": entity_subw_indices_batch}
        _input["input_ids"] = torch.LongTensor(input_ids).to(self.device)
        _input["attention_mask"] = torch.LongTensor(attention_mask).to(self.device)
        _input["labels"] = labels

        self.model.train()
        self.model.zero_grad()
        self.optimizer.zero_grad()  # zero the parameter gradients

        loss, softmax_scores = self.model(**_input)
        loss.backward()
        self.optimizer.step()

        # Clip the norm of the gradients to prevent the "exploding gradients" problem
        if self.clip_norm:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_norm)

        if self.lr_scheduler is not None:
            self.lr_scheduler.step()

        return loss.item()

    def __call__(self, input_ids, attention_mask, entity_subw_indices_batch):

        self.model.eval()
        _input = {"entity_subw_indices": entity_subw_indices_batch}
        _input["input_ids"] = torch.LongTensor(input_ids).to(self.device)
        _input["attention_mask"] = torch.LongTensor(attention_mask).to(self.device)

        with torch.no_grad():
            logits = self.model(**_input)

        probas = torch.nn.functional.softmax(logits, dim=-1)
        probas = probas.detach().cpu().numpy()

        logits = logits.detach().cpu().numpy()
        pred = np.argmax(logits, axis=-1)
        seq_lengths = [len(elem) for elem in entity_subw_indices_batch]
        pred = [pred_elem[:seq_len] for seq_len, pred_elem in zip(seq_lengths, pred)]

        if self.return_probas:
            return pred, probas
        else:
            return pred

    def siamese_ranking_el_model(self, **kwargs) -> nn.Module:
        return SiameseBertElModel(
            pretrained_bert=self.pretrained_bert,
            encoder_save_path=self.encoder_save_path,
            bert_tokenizer_config_file=self.pretrained_bert,
            device=self.device,
            emb_size=self.emb_size,
            n_tags=self.n_tags,
        )

    def save(self, fname: Optional[str] = None, *args, **kwargs) -> None:
        if fname is None:
            fname = self.save_path
        if not fname.parent.is_dir():
            raise ConfigError("Provided save path is incorrect!")
        weights_path = Path(fname).with_suffix(".pth.tar")
        log.info(f"Saving model to {weights_path}.")
        torch.save(
            {
                "model_state_dict": self.model.cpu().state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "epochs_done": self.epochs_done,
            },
            weights_path,
        )
        self.model.to(self.device)
        self.model.save()


class TextEncoder(nn.Module):
    def __init__(
        self,
        pretrained_bert: str,
        emb_size: int,
        n_tags: int,
        bert_tokenizer_config_file: str = None,
        bert_config_file: str = None,
        device: str = "gpu",
    ):
        super().__init__()
        self.pretrained_bert = pretrained_bert
        self.bert_config_file = bert_config_file
        self.encoder, self.config, self.bert_config = None, None, None
        self.device = device
        self.load()
        self.tokenizer = AutoTokenizer.from_pretrained(self.pretrained_bert)
        self.zero_emb = torch.Tensor([0.0 for _ in range(emb_size)]).to(self.device)
        self.fc = nn.Linear(emb_size, n_tags).to(self.device)

    def forward(self, input_ids, attention_mask, entity_subw_indices_batch):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state
        embs_batch = []
        seq_lengths = []
        for n, entity_subw_indices_list in enumerate(entity_subw_indices_batch):
            embs_list = []
            for entity_subw_indices in entity_subw_indices_list:
                embs = []
                for ind in entity_subw_indices:
                    embs.append(hidden_states[n][ind])
                embs_list.append(torch.mean(torch.stack(embs), axis=0))
            seq_lengths.append(len(embs_list))
            embs_batch.append(embs_list)
        max_seq_len = max(seq_lengths)
        for i in range(len(embs_batch)):
            for j in range(max_seq_len - len(embs_batch[i])):
                embs_batch[i].append(self.zero_emb)

        embs_tensors = []
        for embs_list in embs_batch:
            if not embs_list:
                embs_list = [self.zero_emb]
            embs_tensors.append(torch.stack(embs_list))

        embs_tensor = torch.stack(embs_tensors).to(self.device)
        logits = self.fc(embs_tensor)

        return logits

    def load(self) -> None:
        if self.pretrained_bert:
            log.info(f"From pretrained {self.pretrained_bert}.")
            self.pretrained_bert = str(expand_path(self.pretrained_bert))
            self.config = AutoConfig.from_pretrained(self.pretrained_bert, output_hidden_states=True)
            self.encoder = AutoModel.from_pretrained(self.pretrained_bert, config=self.config)

        elif self.bert_config_file and Path(self.bert_config_file).is_file():
            self.config = AutoConfig.from_json_file(str(expand_path(self.bert_config_file)))
            self.encoder = AutoModel.from_config(config=self.bert_config)
        else:
            raise ConfigError("No pre-trained BERT model is given.")
        self.encoder.to(self.device)


class SiameseBertElModel(nn.Module):
    def __init__(
        self,
        encoder_save_path: str,
        emb_size: int,
        n_tags: int,
        pretrained_bert: str = None,
        bert_tokenizer_config_file: str = None,
        bert_config_file: str = None,
        device: str = "gpu",
    ):
        super().__init__()
        self.pretrained_bert = pretrained_bert
        self.encoder_save_path = encoder_save_path
        self.bert_config_file = bert_config_file
        self.device = device
        self.emb_size = emb_size
        self.n_tags = n_tags

        # initialize parameters that would be filled later
        self.encoder = TextEncoder(self.pretrained_bert, emb_size, n_tags, device=self.device)

    def forward(self, input_ids, attention_mask, entity_subw_indices, labels=None):
        logits = self.encoder(input_ids, attention_mask, entity_subw_indices)
        if labels is not None:
            labels_len = [len(elem) for elem in labels]
            max_len = max(labels_len)
            token_attention_mask = [[0 for _ in range(max_len)] for _ in labels]
            for i in range(len(entity_subw_indices)):
                for j in range(len(entity_subw_indices[i])):
                    token_attention_mask[i][j] = 1
            for i in range(len(labels)):
                for j in range(len(labels[i]) - len(entity_subw_indices[i])):
                    labels[i][j] = -1

            token_attention_mask = torch.LongTensor(token_attention_mask).to(self.device)
            labels = torch.LongTensor(labels).to(self.device)

            loss_fct = torch.nn.CrossEntropyLoss(ignore_index=-1)

            if token_attention_mask is not None:
                active_loss = token_attention_mask.view(-1) == 1
                active_logits = logits.view(-1, self.n_tags)
                active_labels = torch.where(
                    active_loss, labels.view(-1), torch.tensor(loss_fct.ignore_index).type_as(labels)
                )
                loss = loss_fct(active_logits, active_labels)
            else:
                loss = loss_fct(logits.view(-1, self.n_tags), labels.view(-1))
            return loss, logits
        else:
            return logits

    def save(self) -> None:
        encoder_weights_path = expand_path(self.encoder_save_path).with_suffix(".pth.tar")
        log.info(f"Saving encoder to {encoder_weights_path}.")
        torch.save({"model_state_dict": self.encoder.cpu().state_dict()}, encoder_weights_path)
        self.encoder.to(self.device)
