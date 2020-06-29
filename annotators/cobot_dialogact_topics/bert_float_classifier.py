import logging
from os import getenv
from typing import List, Union

import sentry_sdk
from bert_dp.preprocessing import InputFeatures
from overrides import overrides

from deeppavlov.core.common.registry import register
from deeppavlov.models.bert.bert_classifier import BertClassifierModel

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@register("bert_float_classifier")
class BertFloatClassifierModel(BertClassifierModel):
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
        topics = ['Other', 'Phatic', 'Entertainment_Movies',
                  'Entertainment_Books', 'Entertainment_General', 'Interactive',
                  'nan', 'Sports', 'Entertainment_Music',
                  'Science_and_Technology', 'Politics']
        # Order DOES matter
        if not self.return_probas:
            pred = self.sess.run(self.y_predictions, feed_dict=feed_dict)
        else:
            pred = self.sess.run(self.y_probas, feed_dict=feed_dict)
        alpha = 1.1  # we introduce alpha to increase the probability of rare classes
        for i in range(len(pred)):
            pred[i] = [min(alpha * j, 0.99) for j in pred[i]]
        prediction_list = []
        for prediction in pred:
            topic_list = []
            for i in range(len(prediction)):
                if prediction[i] > 0.5:
                    topic_list.append(topics[i])
            prediction_list.append(topic_list)
        logging.info('Predictions from cobot dialogact topics are ' + str(prediction_list))
        return pred
