import logging
from os import getenv

import sentry_sdk

from deeppavlov.core.common.registry import register
from deeppavlov.models.bert.bert_classifier import BertClassifierModel

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@register("tf_breakdown_classifier")
class CustomClassifierModel(BertClassifierModel):
    columns = ["breakdown", "no_breakdown"]

    def __call__(self, features):
        """
        Make prediction for given features (texts).

        Args:
            features: batch of InputFeatures

        Returns:
            predicted classes or probabilities of each class

        """
        pred = super().__call__(features=features)

        batch_predictions = []
        for i in range(len(pred)):
            batch_predictions.append({self.columns[j]: float(pred[i, j]) for j in range(len(self.columns))})

        return batch_predictions
