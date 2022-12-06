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

import logging
from os import getenv
from typing import List, Union

# import sentry_sdk
from bert_dp.preprocessing import InputFeatures
from overrides import overrides

from deeppavlov.core.common.registry import register
from deeppavlov.models.bert.bert_classifier import BertClassifierModel

# sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@register("emotion_classification")
class BertFloatClassifierModel(BertClassifierModel):
    """
    Bert-based model for text classification with floating point values

    It uses output from [CLS] token and predicts labels using linear transformation.

    """

    all_columns = ["anger", "fear", "joy", "love", "sadness", "surprise", "neutral"]
    used_columns = all_columns  # ["neutral", "very_positive", "very_negative"]

    # map2base_sentiment = []  # {"neutral": "neutral", "very_positive": "positive", "very_negative": "negative"}

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # FOR INIT GRAPH when training was used the following loss function
        # we have multi-label case
        # some classes for some samples are true-labeled as `-1`
        # we should not take into account (loss) this values
        # self.y_probas = tf.nn.sigmoid(logits)
        # chosen_inds = tf.not_equal(one_hot_labels, -1)
        #
        # self.loss = tf.reduce_mean(
        #     tf.nn.sigmoid_cross_entropy_with_logits(labels=one_hot_labels, logits=logits)[chosen_inds])

    @overrides
    def __call__(self, features: List[InputFeatures]) -> Union[List[int], List[List[float]]]:
        """
        Make prediction for given features (texts).

        Args:
            features: batch of InputFeatures

        Returns:
            predicted classes or probabilities of each class

        """
        logging.info(features)
        input_ids = [f.input_ids for f in features]
        input_masks = [f.input_mask for f in features]
        input_type_ids = [f.input_type_ids for f in features]

        feed_dict = self._build_feed_dict(input_ids, input_masks, input_type_ids)
        if not self.return_probas:
            pred = self.sess.run(self.y_predictions, feed_dict=feed_dict)
        else:
            pred = self.sess.run(self.y_probas, feed_dict=feed_dict)
        batch_predictions = [{column: prob for column, prob in zip(self.used_columns, curr_pred)} for curr_pred in pred]
        return batch_predictions
