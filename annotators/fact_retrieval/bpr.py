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


import faiss
import logging
import time
import os
import numpy as np
import torch
from tqdm import trange
from transformers import AutoTokenizer

import sentry_sdk
from biencoder import BiEncoder
from index import FaissBinaryIndex, FaissIndex

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.models.serializable import Serializable

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Retriever(object):
    def __init__(self, index: FaissIndex, biencoder: BiEncoder):
        self.index = index
        self._biencoder = biencoder
        self._tokenizer = AutoTokenizer.from_pretrained(biencoder.hparams.base_pretrained_model, use_fast=True)

    def encode_queries(self, queries, batch_size: int = 256) -> np.ndarray:
        embeddings = []
        with torch.no_grad():
            for start in trange(0, len(queries), batch_size):
                model_inputs = self._tokenizer.batch_encode_plus(
                    queries[start : start + batch_size],
                    return_tensors="pt",
                    max_length=self._biencoder.hparams.max_query_length,
                    padding="max_length",
                )

                model_inputs = {k: v.to(self._biencoder.device) for k, v in model_inputs.items()}
                emb = self._biencoder.query_encoder(**model_inputs).cpu().numpy()
                embeddings.append(emb)

        return np.vstack(embeddings)

    def search(self, query_embeddings: np.ndarray, k: int, **faiss_index_options):
        scores_list, ids_list = self.index.search(query_embeddings, k, **faiss_index_options)
        return scores_list, ids_list


@register("bpr")
class BPR(Component, Serializable):
    def __init__(
        self,
        pretrained_model,
        load_path,
        bpr_index,
        query_encoder_file,
        top_n=100,
        nprobe=10,
        device: str = "gpu",
        *args,
        **kwargs,
    ):
        super().__init__(save_path=None, load_path=load_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() and device == "gpu" else "cpu")
        self.bpr_index = bpr_index
        self.top_n = top_n
        self.nprobe = nprobe
        self.hparams = {
            "base_pretrained_model": pretrained_model,
            "load_path": f"{self.load_path}/{query_encoder_file}",
            "max_query_length": 256,
            "num_hard_negatives": 1,
            "num_other_negatives": 0,
        }
        self.load()
        self.index = FaissBinaryIndex(self.base_index)
        self.retriever = Retriever(self.index, self.biencoder)

    def load(self):
        self.biencoder = BiEncoder(self.hparams)
        checkpoint = torch.load(self.hparams["load_path"], map_location=self.device)
        self.biencoder.query_encoder.load_state_dict(checkpoint["model_state_dict"], strict=False)
        self.biencoder.eval()
        self.biencoder.freeze()
        self.base_index = faiss.read_index_binary(str(self.load_path / self.bpr_index))
        self.base_index.nprobe = self.nprobe

    def save(self) -> None:
        pass

    def __call__(self, queries):
        queries = list(queries)
        queries = [query.lower() for query in queries]
        query_embeddings = self.retriever.encode_queries(queries)
        tm1 = time.time()
        scores_batch, ids_batch = self.retriever.search(query_embeddings, k=self.top_n)
        tm2 = time.time()
        logger.info(f"time of ranking {tm2 - tm1}")
        ids_batch = ids_batch.tolist()

        return [ids_batch]
