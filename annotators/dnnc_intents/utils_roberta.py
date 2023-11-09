from deeppavlov.core.models.component import Component
from deeppavlov.core.common.registry import register
from deeppavlov.models.torch_bert.torch_transformers_classifier import TorchTransformersClassifierModel

from typing import Dict, Union, List, Tuple
import json
import os
import numpy as np
import torch
import time
import logging

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logger = logging.getLogger(__name__)


supported_intents = os.getenv("CLASSES").split(",")


@register("dnnc_preparer")
class dnnc_preparer(Component):
    def __init__(self, thr_class=10, thr_oos=50, **kwargs):
        self.data = json.load(open("data_full.json", "r"))
        cnt = dict()
        train_data = []
        for elem in self.data["val"] + self.data["oos_val"]:
            class_ = elem[1]
            if any(
                [
                    cnt.get(class_, 0) < thr_class and class_ in supported_intents,
                    (class_ == "oos" and cnt.get(class_, 0) < thr_oos),
                ]
            ):
                train_data.append(elem)
            cnt[class_] = cnt.get(class_, 0) + 1
        self.data = train_data

    def __call__(self, texts):
        return texts, self.data


@register("torch_transformers_classifier_batch1")
class TorchTransformersClassifierModelBatch1(TorchTransformersClassifierModel):
    def __call__(self, features: Dict[str, torch.tensor]) -> Union[List[int], List[List[float]]]:
        """Make prediction for given features (texts).

        Args:
            features: batch of InputFeatures

        Returns:
            predicted classes or probabilities of each class

        """
        answer = []
        logger.debug(len(features["input_ids"]))
        t = time.time()
        for i in range(len(features["input_ids"])):
            _input = {key: value[i].unsqueeze(0).to(self.device) for key, value in features.items()}

            with torch.no_grad():
                tokenized = {key: value for (key, value) in _input.items() if key in self.accepted_keys}

                # Forward pass, calculate logit predictions
                logits = self.model(**tokenized)
                logits = logits[0]

            if self.return_probas:
                if self.is_binary:
                    pred = torch.sigmoid(logits).squeeze(1)
                elif not self.multilabel:
                    pred = torch.nn.functional.softmax(logits, dim=-1)
                else:
                    pred = torch.nn.functional.sigmoid(logits)
                pred = pred.detach().cpu().numpy()
            elif self.n_classes > 1:
                logits = logits.detach().cpu().numpy()
                pred = np.argmax(logits, axis=1)
            # regression
            else:
                pred = logits.squeeze(-1).detach().cpu().numpy()
            answer.append(pred)
        logger.debug(time.time() - t)
        answer = np.concatenate(answer)
        return answer


@register("dnnc_pairgenerator")
class PairGenerator(Component):
    """
    Generates all possible ordered pairs from 'texts_batch' and 'support_dataset'

    Args:
        bidirectional: adds pairs in reverse order
    """

    def __init__(self, bidirectional: bool = False, **kwargs) -> None:
        self.bidirectional = bidirectional

    def __call__(
        self,
        texts: List[str],
        dataset: List[List[str]],
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        hypotesis_batch = []
        premise_batch = []
        hypotesis_labels_batch = []
        for [premise, [hypotesis, hypotesis_labels]] in zip(
            texts * len(dataset), np.repeat(dataset, len(texts), axis=0)
        ):
            premise_batch.append(premise)
            hypotesis_batch.append(hypotesis)
            hypotesis_labels_batch.append(hypotesis_labels)

            if self.bidirectional:
                premise_batch.append(hypotesis)
                hypotesis_batch.append(premise)
                hypotesis_labels_batch.append(hypotesis_labels)
        return texts, hypotesis_batch, premise_batch, hypotesis_labels_batch
