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

import re
from logging import getLogger
from pathlib import Path
from typing import List, Optional, Dict

import torch
from overrides import overrides
from transformers import AutoConfig, AutoTokenizer
from transformers import T5ForConditionalGeneration

from deeppavlov.core.common.errors import ConfigError
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.torch_model import TorchModel

logger = getLogger(__name__)


def softmax_mask(val, mask):
    inf = 1e30
    return -inf * (1 - mask.to(torch.float32)) + val


@register("t5_generative_ie")
class T5GenerativeIE(TorchModel):
    def __init__(
        self,
        pretrained_transformer: str,
        attention_probs_keep_prob: Optional[float] = None,
        add_special_tokens: List[str] = None,
        hidden_keep_prob: Optional[float] = None,
        optimizer: str = "AdamW",
        optimizer_parameters: Optional[dict] = None,
        bert_config_file: Optional[str] = None,
        learning_rate_drop_patience: int = 20,
        learning_rate_drop_div: float = 2.0,
        load_before_drop: bool = True,
        clip_norm: Optional[float] = None,
        min_learning_rate: float = 1e-06,
        generate_max_length: int = 50,
        top_n: int = 1,
        batch_decode: bool = False,
        scores_thres: float = -0.17,
        device: str = "cpu",
        **kwargs,
    ) -> None:

        if not optimizer_parameters:
            optimizer_parameters = {"lr": 0.01, "weight_decay": 0.01, "betas": (0.9, 0.999), "eps": 1e-6}
        self.generate_max_length = generate_max_length

        self.attention_probs_keep_prob = attention_probs_keep_prob
        self.hidden_keep_prob = hidden_keep_prob
        self.clip_norm = clip_norm

        self.pretrained_transformer = pretrained_transformer
        self.bert_config_file = bert_config_file
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_transformer, do_lower_case=False)
        special_tokens_dict = {"additional_special_tokens": add_special_tokens}
        self.tokenizer.add_special_tokens(special_tokens_dict)
        self.replace_tokens = [("<pad>", ""), ("</s>", ""), ("<extra_id_0>", "")]
        self.top_n = top_n
        self.batch_decode = batch_decode
        self.scores_thres = scores_thres

        super().__init__(
            device=device,
            optimizer=optimizer,
            optimizer_parameters=optimizer_parameters,
            learning_rate_drop_patience=learning_rate_drop_patience,
            learning_rate_drop_div=learning_rate_drop_div,
            load_before_drop=load_before_drop,
            min_learning_rate=min_learning_rate,
            **kwargs,
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() and device == "gpu" else "cpu")

    def train_on_batch(self, input_ids_batch, attention_mask_batch, target_ids_batch) -> Dict:
        input_ids_batch = torch.LongTensor(input_ids_batch).to(self.device)
        attention_mask_batch = torch.LongTensor(attention_mask_batch).to(self.device)
        target_ids_batch = torch.LongTensor(target_ids_batch).to(self.device)
        input_ = {"input_ids": input_ids_batch, "attention_mask": attention_mask_batch, "labels": target_ids_batch}

        self.optimizer.zero_grad()
        loss = self.model(**input_)[0]
        if self.is_data_parallel:
            loss = loss.mean()
        loss.backward()
        # Clip the norm of the gradients to 1.0.
        # This is to help prevent the "exploding gradients" problem.
        if self.clip_norm:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_norm)

        self.optimizer.step()
        if self.lr_scheduler is not None:
            self.lr_scheduler.step()

        return {"loss": loss.item()}

    @property
    def is_data_parallel(self) -> bool:
        return isinstance(self.model, torch.nn.DataParallel)

    def __call__(self, input_ids_batch, attention_mask_batch):
        model = self.model.module if hasattr(self.model, "module") else self.model
        if self.batch_decode:
            input_ids_batch = torch.LongTensor(input_ids_batch).to(self.device)
            attention_mask_batch = torch.LongTensor(attention_mask_batch).to(self.device)
            input_ = {
                "input_ids": input_ids_batch,
                "attention_mask": attention_mask_batch,
            }
            with torch.no_grad():
                answer_ids_batch = model.generate(**input_)
            init_answers_batch = self.tokenizer.batch_decode(answer_ids_batch, skip_special_tokens=False)
            answers_batch = []
            for answer in init_answers_batch:
                for old_tok, new_tok in self.replace_tokens:
                    answer = answer.replace(old_tok, new_tok)
                answers_batch.append(answer)
            return answers_batch
        else:
            answers_batch, scores_batch = [], []
            for input_ids in input_ids_batch:
                input_ids = torch.LongTensor([input_ids]).to(self.device)
                with torch.no_grad():
                    outputs = model.generate(
                        input_ids,
                        num_beams=5,
                        num_return_sequences=self.top_n,
                        return_dict_in_generate=True,
                        output_scores=True,
                    )
                    sequences = outputs.sequences
                    scores = outputs.sequences_scores
                    scores = scores.cpu().numpy().tolist()
                    answers = [self.tokenizer.decode(output, skip_special_tokens=False) for output in sequences]
                    logger.info(f"triplets {answers} scores {scores}")
                    processed_answers, processed_scores = [], []
                    for answer, score in zip(answers, scores):
                        if score > self.scores_thres:
                            for old_tok, new_tok in self.replace_tokens:
                                answer = answer.replace(old_tok, new_tok)
                            processed_answers.append(answer)
                            processed_scores.append(score)
                if self.top_n == 1:
                    if processed_answers:
                        answers_batch.append(processed_answers[0])
                        scores_batch.append(processed_scores[0])
                    else:
                        answers_batch.append("")
                        scores_batch.append(0.0)
                else:
                    answers_batch.append(processed_answers)
                    scores_batch.append(processed_scores)
            return answers_batch, scores_batch

    @overrides
    def load(self, fname=None):
        if fname is not None:
            self.load_path = fname

        if self.pretrained_transformer:
            logger.info(f"From pretrained {self.pretrained_transformer}.")
            config = AutoConfig.from_pretrained(
                self.pretrained_transformer, output_attentions=False, output_hidden_states=False
            )

            self.model = T5ForConditionalGeneration.from_pretrained(self.pretrained_transformer, config=config)

        elif self.bert_config_file and Path(self.bert_config_file).is_file():
            self.bert_config = AutoConfig.from_json_file(str(expand_path(self.bert_config_file)))

            if self.attention_probs_keep_prob is not None:
                self.bert_config.attention_probs_dropout_prob = 1.0 - self.attention_probs_keep_prob
            if self.hidden_keep_prob is not None:
                self.bert_config.hidden_dropout_prob = 1.0 - self.hidden_keep_prob
            self.model = T5ForConditionalGeneration(config=self.bert_config)
        else:
            raise ConfigError("No pre-trained BERT model is given.")

        if self.device.type == "cuda" and torch.cuda.device_count() > 1:
            self.model = torch.nn.DataParallel(self.model)

        self.model.to(self.device)

        self.optimizer = getattr(torch.optim, self.optimizer_name)(self.model.parameters(), **self.optimizer_parameters)

        if self.lr_scheduler_name is not None:
            self.lr_scheduler = getattr(torch.optim.lr_scheduler, self.lr_scheduler_name)(
                self.optimizer, **self.lr_scheduler_parameters
            )

        if self.load_path:
            logger.info(f"Load path {self.load_path} is given.")
            if isinstance(self.load_path, Path) and not self.load_path.parent.is_dir():
                raise ConfigError("Provided load path is incorrect!")

            weights_path = Path(self.load_path.resolve())
            weights_path = weights_path.with_suffix(".pth.tar")
            if weights_path.exists():
                logger.info(f"Load path {weights_path} exists.")
                logger.info(f"Initializing `{self.__class__.__name__}` from saved.")

                # now load the weights, optimizer from saved
                logger.info(f"Loading weights from {weights_path}.")
                checkpoint = torch.load(weights_path, map_location=self.device)
                model_state = checkpoint["model_state_dict"]
                optimizer_state = checkpoint["optimizer_state_dict"]

                # load a multi-gpu model on a single device
                if not self.is_data_parallel and "module." in list(model_state.keys())[0]:
                    tmp_model_state = {}
                    for key, value in model_state.items():
                        tmp_model_state[re.sub("module.", "", key)] = value
                    model_state = tmp_model_state

                strict_load_flag = bool(
                    [key for key in checkpoint["model_state_dict"].keys() if key.endswith("embeddings.position_ids")]
                )
                self.model.load_state_dict(model_state, strict=strict_load_flag)
                self.optimizer.load_state_dict(optimizer_state)
                self.epochs_done = checkpoint.get("epochs_done", 0)
            else:
                logger.info(f"Init from scratch. Load path {weights_path} does not exist.")
