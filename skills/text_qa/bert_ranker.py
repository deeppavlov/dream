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

from operator import itemgetter
import math
from typing import Iterable, Optional, Any, Union, Tuple
from enum import IntEnum

import tensorflow as tf
import numpy as np
from bert_dp.modeling import BertConfig, BertModel

from collections import defaultdict
from logging import getLogger
from typing import Iterable, Tuple

from tensorflow.python.ops import variables

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.errors import ConfigError
from deeppavlov.core.common.registry import cls_from_str
from deeppavlov.core.models.tf_model import NNModel, TfModelMeta

logger = getLogger(__name__)


class TFModel(NNModel, metaclass=TfModelMeta):
    """Parent class for all components using TensorFlow."""

    sess: tf.Session

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def load(self, exclude_scopes: tuple = ('Optimizer',)) -> None:
        """Load model parameters from self.load_path"""
        if not hasattr(self, 'sess'):
            raise RuntimeError('Your TensorFlow model {} must'
                               ' have sess attribute!'.format(self.__class__.__name__))
        path = str(self.load_path.resolve())
        # Check presence of the model files
        if tf.train.checkpoint_exists(path):
            logger.info('[loading model from {}]'.format(path))
            # Exclude optimizer variables from saved variables
            var_list = self._get_saveable_variables(exclude_scopes)
            saver = tf.train.Saver(var_list)
            saver.restore(self.sess, path)

    def deserialize(self, weights: Iterable[Tuple[str, np.ndarray]]) -> None:
        assign_ops = []
        feed_dict = {}
        for var_name, value in weights:
            var = self.sess.graph.get_tensor_by_name(var_name)
            value = np.asarray(value)
            assign_placeholder = tf.placeholder(var.dtype, shape=value.shape)
            assign_op = tf.assign(var, assign_placeholder)
            assign_ops.append(assign_op)
            feed_dict[assign_placeholder] = value
        self.sess.run(assign_ops, feed_dict=feed_dict)

    def save(self, exclude_scopes: tuple = ('Optimizer',)) -> None:
        """Save model parameters to self.save_path"""
        if not hasattr(self, 'sess'):
            raise RuntimeError('Your TensorFlow model {} must'
                               ' have sess attribute!'.format(self.__class__.__name__))
        path = str(self.save_path.resolve())
        logger.info('[saving model to {}]'.format(path))
        var_list = self._get_saveable_variables(exclude_scopes)
        saver = tf.train.Saver(var_list)
        saver.save(self.sess, path)

    def serialize(self) -> Tuple[Tuple[str, np.ndarray], ...]:
        tf_vars = tf.global_variables()
        values = self.sess.run(tf_vars)
        return tuple(zip([var.name for var in tf_vars], values))

    @staticmethod
    def _get_saveable_variables(exclude_scopes=tuple()):
        # noinspection PyProtectedMember
        all_vars = variables._all_saveable_objects()
        vars_to_train = [var for var in all_vars if all(sc not in var.name for sc in exclude_scopes)]
        return vars_to_train

    @staticmethod
    def _get_trainable_variables(exclude_scopes=tuple()):
        all_vars = tf.global_variables()
        vars_to_train = [var for var in all_vars if all(sc not in var.name for sc in exclude_scopes)]
        return vars_to_train

    def get_train_op(self,
                     loss,
                     learning_rate,
                     optimizer=None,
                     clip_norm=None,
                     learnable_scopes=None,
                     optimizer_scope_name=None,
                     **kwargs):
        """
        Get train operation for given loss

        Args:
            loss: loss, tf tensor or scalar
            learning_rate: scalar or placeholder.
            clip_norm: clip gradients norm by clip_norm.
            learnable_scopes: which scopes are trainable (None for all).
            optimizer: instance of tf.train.Optimizer, default Adam.
            **kwargs: parameters passed to tf.train.Optimizer object
               (scalars or placeholders).

        Returns:
            train_op
        """
        if optimizer_scope_name is None:
            opt_scope = tf.variable_scope('Optimizer')
        else:
            opt_scope = tf.variable_scope(optimizer_scope_name)
        with opt_scope:
            if learnable_scopes is None:
                variables_to_train = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
            else:
                variables_to_train = []
                for scope_name in learnable_scopes:
                    variables_to_train.extend(tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=scope_name))

            if optimizer is None:
                optimizer = tf.train.AdamOptimizer(learning_rate, **kwargs)

            # For batch norm it is necessary to update running averages
            extra_update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(extra_update_ops):

                def clip_if_not_none(grad):
                    if grad is not None:
                        return tf.clip_by_norm(grad, clip_norm)

                opt = optimizer(learning_rate, **kwargs)
                grads_and_vars = opt.compute_gradients(loss, var_list=variables_to_train)
                if clip_norm is not None:
                    grads_and_vars = [(clip_if_not_none(grad), var)
                                      for grad, var in grads_and_vars]
                train_op = opt.apply_gradients(grads_and_vars)
        return train_op

    @staticmethod
    def print_number_of_parameters():
        """
        Print number of *trainable* parameters in the network
        """
        logger.info('Number of parameters: ')
        variables = tf.trainable_variables()
        blocks = defaultdict(int)
        for var in variables:
            # Get the top level scope name of variable
            block_name = var.name.split('/')[0]
            number_of_parameters = np.prod(var.get_shape().as_list())
            blocks[block_name] += number_of_parameters
        for block_name, cnt in blocks.items():
            logger.info("{} - {}.".format(block_name, cnt))
        total_num_parameters = np.sum(list(blocks.values()))
        logger.info('Total number of parameters equal {}'.format(total_num_parameters))

    def destroy(self):
        for k in list(self.sess.graph.get_all_collection_keys()):
            self.sess.graph.clear_collection(k)


class DecayType(IntEnum):
    ''' Data class, each decay type is assigned a number. '''
    NO = 1
    LINEAR = 2
    COSINE = 3
    EXPONENTIAL = 4
    POLYNOMIAL = 5
    ONECYCLE = 6
    TRAPEZOID = 7

    @classmethod
    def from_str(cls, label: str):
        label_norm = label.replace('1', 'one').upper()
        if label_norm in cls.__members__:
            return DecayType[label_norm]
        else:
            raise NotImplementedError


class DecayScheduler():
    '''
    Given initial and endvalue, this class generates the next value
    depending on decay type and number of iterations. (by calling next_val().)
    '''

    def __init__(self, dec_type: Union[str, DecayType], start_val: float,
                 num_it: int = None, end_val: float = None, extra: float = None):
        if isinstance(dec_type, DecayType):
            self.dec_type = dec_type
        else:
            self.dec_type = DecayType.from_str(dec_type)
        self.nb, self.extra = num_it, extra
        self.start_val, self.end_val = start_val, end_val
        self.iters = 0
        if self.end_val is None and not (self.dec_type in [1, 4]):
            self.end_val = 0
        if self.dec_type == DecayType.ONECYCLE:
            self.cycle_nb = math.ceil(self.nb / 2)
            self.div = 1.0 if not self.start_val else self.end_val / self.start_val
        if self.dec_type == DecayType.TRAPEZOID:
            self.div = 1.0 if not self.start_val else self.end_val / self.start_val

    def __str__(self):
        return f"DecayScheduler(start_val={self.start_val}, end_val={self.end_val}" \
               f", dec_type={self.dec_type.name}, num_it={self.nb}, extra={self.extra})"

    def next_val(self):
        self.iters = min(self.iters + 1, self.nb)
        # print(f"iters = {self.iters}/{self.nb}")
        if self.dec_type == DecayType.NO:
            return self.start_val
        elif self.dec_type == DecayType.LINEAR:
            pct = self.iters / self.nb
            return self.start_val + pct * (self.end_val - self.start_val)
        elif self.dec_type == DecayType.COSINE:
            cos_out = math.cos(math.pi * self.iters / self.nb) + 1
            return self.end_val + (self.start_val - self.end_val) / 2 * cos_out
        elif self.dec_type == DecayType.EXPONENTIAL:
            ratio = self.end_val / self.start_val
            return self.start_val * (ratio ** (self.iters / self.nb))
        elif self.dec_type == DecayType.POLYNOMIAL:
            delta_val = self.start_val - self.end_val
            return self.end_val + delta_val * (1 - self.iters / self.nb) ** self.extra
        elif self.dec_type == DecayType.ONECYCLE:
            if self.iters > self.cycle_nb:
                # decaying from end_val to start_val for cycle_nb steps
                pct = 1 - (self.iters - self.cycle_nb) / self.cycle_nb
                return self.start_val * (1 + pct * (self.div - 1))
            else:
                # raising from start_val to end_val for cycle_nb steps
                pct = self.iters / self.cycle_nb
                return self.start_val * (1 + pct * (self.div - 1))
        elif self.dec_type == DecayType.TRAPEZOID:
            if self.iters > 0.6 * self.nb:
                # decaying from end_val to start_val for 4/10 * nb steps
                pct = 2.5 * (self.nb - self.iters) / self.nb
                return self.start_val * (1 + pct * (self.div - 1))
            elif self.iters > 0.1 * self.nb:
                # constant end_val
                return self.end_val
            else:
                # raising from start_val to end_val for 1/10 * nb steps
                pct = 10.0 * self.iters / self.nb
                return self.start_val * (1 + pct * (self.div - 1))


DType = Union[str, DecayType]


class LRScheduledTFModel(TFModel):
    """
    TFModel enhanced with optimizer, learning rate and momentum
    management and search.
    """

    def __init__(self,
                 learning_rate: Union[float, Tuple[float, float]] = None,
                 learning_rate_decay: Union[DType, Tuple[DType, Any]] = DecayType.NO,
                 learning_rate_decay_epochs: int = 0,
                 learning_rate_decay_batches: int = 0,
                 learning_rate_drop_div: float = 2.0,
                 learning_rate_drop_patience: int = None,
                 momentum: Union[float, Tuple[float, float]] = None,
                 momentum_decay: Union[DType, Tuple[DType, Any]] = DecayType.NO,
                 momentum_decay_epochs: int = 0,
                 momentum_decay_batches: int = 0,
                 optimizer: str = 'AdamOptimizer',
                 clip_norm: float = None,
                 fit_batch_size: Union[int, str] = None,
                 fit_learning_rate: Tuple[float, float] = [1e-7, 100],
                 fit_learning_rate_div: float = 10.,
                 fit_beta: float = 0.98,
                 fit_min_batches: int = 10,
                 fit_max_batches: int = None,
                 *args, **kwargs) -> None:
        if learning_rate_decay_epochs and learning_rate_decay_batches:
            raise ConfigError("isn't able to update learning rate every batch"
                              " and every epoch sumalteniously")
        if momentum_decay_epochs and momentum_decay_batches:
            raise ConfigError("isn't able to update momentum every batch"
                              " and every epoch sumalteniously")
        super().__init__(*args, **kwargs)

        try:
            self._optimizer = cls_from_str(optimizer)
        except Exception:
            self._optimizer = getattr(tf.train, optimizer.split(':')[-1])
        if not issubclass(self._optimizer, tf.train.Optimizer):
            raise ConfigError("`optimizer` should be tensorflow.train.Optimizer subclass")

        start_val, end_val = learning_rate, None
        if isinstance(learning_rate, (tuple, list)):
            start_val, end_val = learning_rate
        dec_type, extra = learning_rate_decay, None
        if isinstance(learning_rate_decay, (tuple, list)):
            dec_type, extra = learning_rate_decay

        self._lr = start_val
        num_it, self._lr_update_on_batch = learning_rate_decay_epochs, False
        if learning_rate_decay_batches > 0:
            num_it, self._lr_update_on_batch = learning_rate_decay_batches, True

        self._lr_schedule = DecayScheduler(start_val=start_val, end_val=end_val,
                                           num_it=num_it, dec_type=dec_type, extra=extra)
        # self._lr_var = tf.placeholder(tf.float32, shape=[], name='learning_rate')
        self._lr_var = tf.Variable(self._lr or 0., dtype=tf.float32, name='learning_rate')

        if (momentum is None) and \
                self._optimizer not in (tf.train.AdagradDAOptimizer,
                                        tf.train.AdagradOptimizer,
                                        tf.train.GradientDescentOptimizer,
                                        tf.train.ProximalGradientDescentOptimizer,
                                        tf.train.ProximalAdagradOptimizer):
            momentum = 0.9
        start_val, end_val = momentum, None
        if isinstance(momentum, (tuple, list)):
            start_val, end_val = momentum
        dec_type, extra = momentum_decay, None
        if isinstance(momentum_decay, (tuple, list)):
            dec_type, extra = momentum_decay

        self._mom = start_val
        num_it, self._mom_update_on_batch = momentum_decay_epochs, False
        if momentum_decay_batches > 0:
            num_it, self._mom_update_on_batch = momentum_decay_batches, True

        self._mom_schedule = DecayScheduler(start_val=start_val, end_val=end_val,
                                            num_it=num_it, dec_type=dec_type,
                                            extra=extra)
        # self._mom_var = tf.placeholder_with_default(0.9, shape=[], name='momentum')
        # self._mom_var = tf.placeholder(tf.float32, shape=[], name='momentum')
        self._mom_var = tf.Variable(self._mom or 0., dtype=tf.float32, name='momentum')

        self._learning_rate_drop_patience = learning_rate_drop_patience
        self._learning_rate_drop_div = learning_rate_drop_div
        self._learning_rate_cur_impatience = 0.
        self._learning_rate_last_impatience = 0.
        self._learning_rate_cur_div = 1.
        self._clip_norm = clip_norm
        self._fit_batch_size = fit_batch_size
        self._fit_learning_rate = fit_learning_rate
        self._fit_learning_rate_div = fit_learning_rate_div
        self._fit_beta = fit_beta
        self._fit_min_batches = fit_min_batches
        self._fit_max_batches = fit_max_batches
        self._external_lr = False
        self._external_mom = False

    def load(self, exclude_scopes: Optional[Iterable] = ('Optimizer',
                                                         'learning_rate',
                                                         'momentum')):
        return super().load(exclude_scopes=exclude_scopes)

    def fit(self, *args):
        data = list(zip(*args))
        self.save()
        if self._fit_batch_size is None:
            raise ConfigError("in order to use fit() method"
                              " set `fit_batch_size` parameter")
        bs = int(self._fit_batch_size)
        data_len = len(data)
        num_batches = self._fit_max_batches or ((data_len - 1) // bs + 1)

        avg_loss = 0.
        best_loss = float('inf')
        lrs, losses = [], []
        _lr_find_schedule = DecayScheduler(start_val=self._fit_learning_rate[0],
                                           end_val=self._fit_learning_rate[1],
                                           dec_type="exponential",
                                           num_it=num_batches)
        self._lr = _lr_find_schedule.start_val
        self._mom = 0.
        self._update_tf_variables(learning_rate=self._lr, momentum=self._mom)
        best_lr = _lr_find_schedule.start_val
        for i in range(num_batches):
            batch_start = (i * bs) % data_len
            batch_end = batch_start + bs
            report = self.train_on_batch(*zip(*data[batch_start:batch_end]))
            if not isinstance(report, dict):
                report = {'loss': report}
            # Calculating smoothed loss
            avg_loss = self._fit_beta * avg_loss + (1 - self._fit_beta) * report['loss']
            smoothed_loss = avg_loss / (1 - self._fit_beta ** (i + 1))
            lrs.append(self._lr)
            losses.append(smoothed_loss)
            logger.info(f"Batch {i}/{num_batches}: smooth_loss = {smoothed_loss}"
                     f", lr = {self._lr}, best_lr = {best_lr}")
            if math.isnan(smoothed_loss) or (smoothed_loss > 4 * best_loss):
                break
            if (smoothed_loss < best_loss) and (i >= self._fit_min_batches):
                best_loss = smoothed_loss
                best_lr = self._lr
            self._lr = _lr_find_schedule.next_val()
            self._update_tf_variables(learning_rate=self._lr)

            if i >= num_batches:
                break
        # best_lr /= 10
        end_val = self._get_best(lrs, losses)

        start_val = end_val
        if self._lr_schedule.dec_type in (DecayType.ONECYCLE, DecayType.TRAPEZOID):
            start_val = end_val / self._fit_learning_rate_div
        elif self._lr_schedule.dec_type in (DecayType.POLYNOMIAL, DecayType.EXPONENTIAL,
                                            DecayType.LINEAR):
            start_val = end_val
            end_val = end_val / self._fit_learning_rate_div
        self._lr_schedule = DecayScheduler(start_val=start_val,
                                           end_val=end_val,
                                           num_it=self._lr_schedule.nb,
                                           dec_type=self._lr_schedule.dec_type,
                                           extra=self._lr_schedule.extra)
        logger.info(f"Found best learning rate value = {best_lr}"
                 f", setting new learning rate schedule with {self._lr_schedule}.")

        self.load()
        self._lr = self._lr_schedule.start_val
        self._mom = self._mom_schedule.start_val
        self._update_tf_variables(learning_rate=self._lr, momentum=self._mom)
        return {'smoothed_loss': losses, 'learning_rate': lrs}

    @staticmethod
    def _get_best(values, losses, max_loss_div=0.9, min_val_div=10.0):
        assert len(values) == len(losses), "lengths of values and losses should be equal"
        min_ind = np.argmin(losses)
        for i in range(min_ind - 1, 0, -1):
            if (losses[i] * max_loss_div > losses[min_ind]) or \
                    (values[i] * min_val_div < values[min_ind]):
                return values[i + 1]
        return values[min_ind] / min_val_div

    def get_train_op(self,
                     *args,
                     learning_rate: Union[float, tf.placeholder] = None,
                     optimizer: tf.train.Optimizer = None,
                     momentum: Union[float, tf.placeholder] = None,
                     clip_norm: float = None,
                     **kwargs):
        if learning_rate is not None:
            self._external_lr = True
            kwargs['learning_rate'] = learning_rate
        else:
            kwargs['learning_rate'] = self.get_learning_rate_var()
        kwargs['optimizer'] = optimizer or self.get_optimizer()
        kwargs['clip_norm'] = clip_norm or self._clip_norm

        momentum_param = 'momentum'
        if kwargs['optimizer'] == tf.train.AdamOptimizer:
            momentum_param = 'beta1'
        elif kwargs['optimizer'] == tf.train.AdadeltaOptimizer:
            momentum_param = 'rho'

        if momentum is not None:
            self._external_mom = True
            kwargs[momentum_param] = momentum
        elif self.get_momentum() is not None:
            kwargs[momentum_param] = self.get_momentum_var()
        return super().get_train_op(*args, **kwargs)

    def _update_tf_variables(self, learning_rate=None, momentum=None):
        if learning_rate is not None:
            self.sess.run(tf.assign(self._lr_var, learning_rate))
            # log.info(f"Learning rate = {learning_rate}")
        if momentum is not None:
            self.sess.run(tf.assign(self._mom_var, momentum))
            # log.info(f"Momentum      = {momentum}")

    def process_event(self, event_name, data):
        if event_name == "after_validation":
            if data['impatience'] > self._learning_rate_last_impatience:
                self._learning_rate_cur_impatience += 1
            else:
                self._learning_rate_cur_impatience = 0

            self._learning_rate_last_impatience = data['impatience']

            if (self._learning_rate_drop_patience is not None) and \
                    (self._learning_rate_cur_impatience >=
                     self._learning_rate_drop_patience):
                self._learning_rate_cur_impatience = 0
                self._learning_rate_cur_div *= self._learning_rate_drop_div
                self._lr /= self._learning_rate_drop_div
                self._update_tf_variables(learning_rate=self._lr)
                log.info(f"New learning rate divider = {self._learning_rate_cur_div}")
        if event_name == 'after_batch':
            if (self._lr is not None) and self._lr_update_on_batch:
                self._lr = self._lr_schedule.next_val() / self._learning_rate_cur_div
                self._update_tf_variables(learning_rate=self._lr)
            if (self._mom is not None) and self._mom_update_on_batch:
                self._mom = min(1., max(0., self._mom_schedule.next_val()))
                self._update_tf_variables(momentum=self._mom)
        if event_name == 'after_epoch':
            if (self._lr is not None) and not self._lr_update_on_batch:
                self._lr = self._lr_schedule.next_val() / self._learning_rate_cur_div
                self._update_tf_variables(learning_rate=self._lr)
            if (self._mom is not None) and not self._mom_update_on_batch:
                self._mom = min(1., max(0., self._mom_schedule.next_val()))
                self._update_tf_variables(momentum=self._mom)
        if event_name == 'after_train_log':
            if (self._lr is not None) and not self._external_lr:
                data['learning_rate'] = self._lr
            if (self._mom is not None) and not self._external_mom:
                data['momentum'] = self._mom

    def get_learning_rate(self):
        if self._lr is None:
            raise ConfigError("Please specify `learning_rate` parameter"
                              " before training")
        return self._lr

    def get_learning_rate_var(self):
        return self._lr_var

    def get_momentum(self):
        return self._mom

    def get_momentum_var(self):
        return self._mom_var

    def get_optimizer(self):
        return self._optimizer


class BertRankerModel(LRScheduledTFModel):
    # TODO: docs
    # TODO: add head-only pre-training
    def __init__(self, bert_config_file, n_classes, keep_prob,
                 batch_size, num_ranking_samples,
                 one_hot_labels=False,
                 attention_probs_keep_prob=None, hidden_keep_prob=None,
                 pretrained_bert=None,
                 resps=None, resp_vecs=None, resp_features=None, resp_eval=True,
                 conts=None, cont_vecs=None, cont_features=None, cont_eval=True,
                 bot_mode=0, min_learning_rate=1e-06, **kwargs) -> None:
        super().__init__(**kwargs)

        self.batch_size = batch_size
        self.num_ranking_samples = num_ranking_samples
        self.n_classes = n_classes
        self.min_learning_rate = min_learning_rate
        self.keep_prob = keep_prob
        self.one_hot_labels = one_hot_labels
        self.batch_size = batch_size
        self.resp_eval = resp_eval
        self.resps = resps
        self.resp_vecs = resp_vecs
        self.cont_eval = cont_eval
        self.conts = conts
        self.cont_vecs = cont_vecs
        self.bot_mode = bot_mode

        self.bert_config = BertConfig.from_json_file(str(expand_path(bert_config_file)))

        if attention_probs_keep_prob is not None:
            self.bert_config.attention_probs_dropout_prob = 1.0 - attention_probs_keep_prob
        if hidden_keep_prob is not None:
            self.bert_config.hidden_dropout_prob = 1.0 - hidden_keep_prob

        self.sess_config = tf.ConfigProto(allow_soft_placement=True)
        self.sess_config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=self.sess_config)

        self._init_graph()

        self._init_optimizer()

        self.sess.run(tf.global_variables_initializer())

        if pretrained_bert is not None:
            pretrained_bert = str(expand_path(pretrained_bert))

        if tf.train.checkpoint_exists(pretrained_bert) \
                and not tf.train.checkpoint_exists(str(self.load_path.resolve())):
            logger.info('[initializing model with Bert from {}]'.format(pretrained_bert))
            # Exclude optimizer and classification variables from saved variables
            var_list = self._get_saveable_variables(
                exclude_scopes=('Optimizer', 'learning_rate', 'momentum', 'classification'))
            saver = tf.train.Saver(var_list)
            saver.restore(self.sess, pretrained_bert)

        if self.load_path is not None:
            self.load()

        if self.resp_eval:
            assert (self.resps is not None)
            assert (self.resp_vecs is not None)
        if self.cont_eval:
            assert (self.conts is not None)
            assert (self.cont_vecs is not None)
        if self.resp_eval and self.cont_eval:
            assert (len(self.resps) == len(self.conts))

    def _init_graph(self):
        self._init_placeholders()
        with tf.variable_scope("model"):
            self.bert = BertModel(config=self.bert_config,
                                  is_training=self.is_train_ph,
                                  input_ids=self.input_ids_ph,
                                  input_mask=self.input_masks_ph,
                                  token_type_ids=self.token_types_ph,
                                  use_one_hot_embeddings=False,
                                  )

        output_layer_a = self.bert.get_pooled_output()

        with tf.variable_scope("loss"):
            with tf.variable_scope("loss"):
                self.loss = tf.contrib.losses.metric_learning.npairs_loss(self.y_ph, output_layer_a, output_layer_a)
                self.y_probas = output_layer_a

    def _init_placeholders(self):
        self.input_ids_ph = tf.placeholder(shape=(None, None), dtype=tf.int32, name='ids_ph')
        self.input_masks_ph = tf.placeholder(shape=(None, None), dtype=tf.int32, name='masks_ph')
        self.token_types_ph = tf.placeholder(shape=(None, None), dtype=tf.int32, name='token_types_ph')

        if not self.one_hot_labels:
            self.y_ph = tf.placeholder(shape=(None,), dtype=tf.int32, name='y_ph')
        else:
            self.y_ph = tf.placeholder(shape=(None, self.n_classes), dtype=tf.float32, name='y_ph')

        self.learning_rate_ph = tf.placeholder_with_default(0.0, shape=[], name='learning_rate_ph')
        self.keep_prob_ph = tf.placeholder_with_default(1.0, shape=[], name='keep_prob_ph')
        self.is_train_ph = tf.placeholder_with_default(False, shape=[], name='is_train_ph')

    def _init_optimizer(self):
        # TODO: use AdamWeightDecay optimizer
        with tf.variable_scope('Optimizer'):
            self.global_step = tf.get_variable('global_step', shape=[], dtype=tf.int32,
                                               initializer=tf.constant_initializer(0), trainable=False)
            self.train_op = self.get_train_op(self.loss, learning_rate=self.learning_rate_ph)

    def _build_feed_dict(self, input_ids, input_masks, token_types, y=None):
        feed_dict = {
            self.input_ids_ph: input_ids,
            self.input_masks_ph: input_masks,
            self.token_types_ph: token_types,
        }
        if y is not None:
            feed_dict.update({
                self.y_ph: y,
                self.learning_rate_ph: max(self.get_learning_rate(), self.min_learning_rate),
                self.keep_prob_ph: self.keep_prob,
                self.is_train_ph: True,
            })

        return feed_dict

    def train_on_batch(self, features, y):
        pass

    def __call__(self, features_list):
        pred = []
        for features in features_list:
            input_ids = [f.input_ids for f in features]
            input_masks = [f.input_mask for f in features]
            input_type_ids = [f.input_type_ids for f in features]
            feed_dict = self._build_feed_dict(input_ids, input_masks, input_type_ids)
            p = self.sess.run(self.y_probas, feed_dict=feed_dict)
            if len(p.shape) == 1:
                p = np.expand_dims(p, 0)
            pred.append(p)
        pred = np.vstack(pred)
        pred = pred / np.linalg.norm(pred, keepdims=True)
        bs = pred.shape[0]
        if self.bot_mode == 0:
            s = pred @ self.resp_vecs.T
            ids = np.argmax(s, 1)
            ans = [[self.resps[ids[i]] for i in range(bs)], [s[i][ids[i]] for i in range(bs)]]
        if self.bot_mode == 1:
            sr = (pred @ self.resp_vecs.T + 1) / 2
            sc = (pred @ self.cont_vecs.T + 1) / 2
            ids = np.argsort(sr, 1)[:, -10:]
            sc = [sc[i, ids[i]] for i in range(bs)]
            ids = [sorted(zip(ids[i], sc[i]), key=itemgetter(1), reverse=True) for i in range(bs)]
            sc = [list(map(lambda x: x[1], ids[i])) for i in range(bs)]
            ids = [list(map(lambda x: x[0], ids[i])) for i in range(bs)]
            ans = [[self.resps[ids[i][0]] for i in range(bs)], [float(sc[i][0]) for i in range(bs)]]
        if self.bot_mode == 2:
            sr = (pred @ self.resp_vecs.T + 1) / 2
            sc = (pred @ self.cont_vecs.T + 1) / 2
            ids = np.argsort(sc, 1)[:, -10:]
            sr = [sr[i, ids[i]] for i in range(bs)]
            ids = [sorted(zip(ids[i], sr[i]), key=itemgetter(1), reverse=True) for i in range(bs)]
            sr = [list(map(lambda x: x[1], ids[i])) for i in range(bs)]
            ids = [list(map(lambda x: x[0], ids[i])) for i in range(bs)]
            ans = [[self.resps[ids[i][0]] for i in range(bs)], [float(sr[i][0]) for i in range(bs)]]
        if self.bot_mode == 3:
            sr = pred @ self.resp_vecs.T
            sc = pred @ self.cont_vecs.T
            s = sr + sc
            ids = np.argmax(s, 1)
            ans = [[self.resps[ids[i]] for i in range(bs)], [float(s[i][ids[i]]) for i in range(bs)]]
        return ans
