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

import sentry_sdk
from bert_dp.preprocessing import InputFeatures, InputExample
from bert_dp.tokenization import FullTokenizer
from overrides import overrides
from deeppavlov.core.models.component import Component
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.models.bert.bert_classifier import BertClassifierModel

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@register('bert_preprocessor')
class BertPreprocessor(Component):
    """Tokenize text on subtokens, encode subtokens with their indices, create tokens and segment masks.
    Check details in :func:`bert_dp.preprocessing.convert_examples_to_features` function.
    Args:
        vocab_file: path to vocabulary
        do_lower_case: set True if lowercasing is needed
        max_seq_length: max sequence length in subtokens, including [SEP] and [CLS] tokens
    Attributes:
        max_seq_length: max sequence length in subtokens, including [SEP] and [CLS] tokens
        tokenizer: instance of Bert FullTokenizer
    """

    def __init__(self,
                 vocab_file: str,
                 do_lower_case: bool = True,
                 max_seq_length: int = 128,
                 **kwargs) -> None:
        self.max_seq_length = max_seq_length
        vocab_file = str(expand_path(vocab_file))
        self.tokenizer = FullTokenizer(vocab_file=vocab_file,
                                       do_lower_case=do_lower_case)

    def __call__(self, texts_a: List[str], texts_b=None) -> List[InputFeatures]:
        """Call Bert :func:`bert_dp.preprocessing.convert_examples_to_features` function to tokenize and create masks.
        texts_a and texts_b are separated by [SEP] token
        Args:
            texts_a: list of texts,
            texts_b: list of texts, it could be None, e.g. single sentence classification task
        Returns:
            batch of :class:`bert_dp.preprocessing.InputFeatures`
            with subtokens, subtoken ids, subtoken mask, segment mask.
        """

        texts_b = [None] * len(texts_a)
        # unique_id is not used
        examples = [InputExample(unique_id=0, text_a=text_a, text_b=text_b)
                    for text_a, text_b in zip(texts_a, texts_b)]
        return convert_examples_to_features(examples, self.max_seq_length, self.tokenizer)


def convert_examples_to_features(examples, seq_length, tokenizer):
    """Loads a data file into a list of `InputBatch`s."""

    features = []
    for (ex_index, example) in enumerate(examples):
        phrases = example.text_a.split('[SEP]')
        tokenized_phrases = [tokenizer.tokenize(phrase) for phrase in phrases]
        # Truncate to max_seq_lenght

        # The convention in BERT is:
        # (a) For sequence pairs:
        #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
        #  type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
        # (b) For single sequences:
        #  tokens:   [CLS] the dog is hairy . [SEP]
        #  type_ids: 0     0   0   0  0     0 0
        #
        # Where "type_ids" are used to indicate whether this is the first
        # sequence or the second sequence. The embedding vectors for `type=0` and
        # `type=1` were learned during pre-training and are added to the wordpiece
        # embedding vector (and position vector). This is not *strictly* necessary
        # since the [SEP] token unambiguously separates the sequences, but it makes
        # it easier for the model to learn the concept of sequences.
        #
        # For classification tasks, the first vector (corresponding to [CLS]) is
        # used as as the "sentence vector". Note that this only makes sense because
        # the entire model is fine-tuned.
        tokens = []
        input_type_ids = []
        tokens.append("[CLS]")
        input_type_ids.append(0)
        for tokenized_phrase in tokenized_phrases:
            for token in tokenized_phrase:
                tokens.append(token)
                input_type_ids.append(0)
            tokens.append("[SEP]")
            input_type_ids.append(0)
        if len(tokens) > seq_length:
            tokens = tokens[len(tokens) - seq_length:]
            input_type_ids = input_type_ids[len(input_type_ids) - seq_length:]
        input_ids = tokenizer.convert_tokens_to_ids(tokens)
        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        input_mask = [1] * len(input_ids)

        # Zero-pad up to the sequence length.
        while len(input_ids) < seq_length:
            input_ids.append(0)
            input_mask.append(0)
            input_type_ids.append(0)

        assert len(input_ids) == seq_length
        assert len(input_mask) == seq_length
        assert len(input_type_ids) == seq_length

        features.append(
            InputFeatures(
                unique_id=example.unique_id,
                tokens=tokens,
                input_ids=input_ids,
                input_mask=input_mask,
                input_type_ids=input_type_ids))
    return features


@register("stop_detect")
class BertFloatClassifierModel(BertClassifierModel):
    """
    Bert-based model for text classification with floating point values

    It uses output from [CLS] token and predicts labels using linear transformation.

    """

    all_columns = ['stop', 'continue']
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
        logging.info("STOP_DETECT_DEBUG")
        input_ids = [f.input_ids for f in features]
        flattened_ids = [i for j in input_ids for i in j]
        logging.info('SEP: ' + str(flattened_ids.count(102)))
        logging.info('[]: ' + str(flattened_ids.count(164)) + str(flattened_ids.count(166)))
        input_masks = [f.input_mask for f in features]
        input_type_ids = [f.input_type_ids for f in features]

        feed_dict = self._build_feed_dict(input_ids, input_masks, input_type_ids)
        if not self.return_probas:
            pred = self.sess.run(self.y_predictions, feed_dict=feed_dict)
        else:
            pred = self.sess.run(self.y_probas, feed_dict=feed_dict)
        batch_predictions = [{column: prob
                              for column, prob in zip(self.used_columns, curr_pred)}
                             for curr_pred in pred]
        return batch_predictions
