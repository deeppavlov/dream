import torch
from torch import nn
import wandb
from tqdm import tqdm
from pathlib import Path
import logging

from src.utils import loss
from src.utils.misc import to_gpu

from src.model_utils.thswad import THWADModel


LOGGER = logging.getLogger('trainer_logger')
logging.basicConfig(level=logging.INFO)


def rec_to_gpu(value):
    if hasattr(value, 'cuda'):
        return to_gpu(value)
    elif isinstance(value, dict):
        return {k: rec_to_gpu(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [rec_to_gpu(v) for v in value]
    else:
        return value


class BaseTrainer(object):
    def __init__(
            self,
            model: THWADModel,
            optimizer: torch.optim.Optimizer,
            scheduler,
            log_interval: int = 5,
            save_path: str = 'model_checkpoints',
            verbose: bool = True,
    ):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.log_interval = log_interval
        self.save_path = Path(save_path)
        self.verbose = verbose

    def _train_step(self, batch_idx, batch):
        raise NotImplementedError

    def train_epoch(self, dataloader, epoch=0):
        self.model.train()
        for batch_idx, batch in enumerate(
                tqdm(dataloader, total=len(dataloader), desc=f'Training {epoch}'),
        ):
            self.optimizer.zero_grad()
            batch = rec_to_gpu(batch)
            loss_dict = self._train_step(batch_idx, batch)
            self.optimizer.step()
            self.scheduler.step()
            if self.verbose and batch_idx % self.log_interval == 0:
                wandb.log({'train': loss_dict})

    def save_model(self, path_postfix):
        self.model.save(self.save_path / f'model_{path_postfix}.pt')

    def train(self, train_dataloader, epochs, val_dataloader=None):
        best_metric = {}
        for epoch in range(epochs):
            self.train_epoch(train_dataloader, epoch)
            if val_dataloader is not None:
                metric = self.test(val_dataloader)
                if self.is_first_metric_better(metric, best_metric):
                    self.save_model('best')
                    best_metric = metric
                if self.should_early_stop(metric):
                    LOGGER.info(f'stopping at epoch: {epoch} with metrics: {metric}')
                    break

        self.save_model('last')
        return best_metric

    def _mean_metrics(self, losses_list_dict):
        mean_loss = {}
        for loss_name, loss_values in losses_list_dict.items():
            mean_loss[loss_name] = torch.mean(torch.stack(loss_values)).item()

        return mean_loss

    def _add_metric(self, loss_dict, single_loss_dict):
        for loss_name, loss_value in single_loss_dict.items():
            if loss_name not in loss_dict:
                loss_dict[loss_name] = []
            loss_dict[loss_name].append(loss_value)

        return loss_dict

    def _test_step(self, batch_idx, batch):
        raise NotImplementedError

    def is_first_metric_better(self, metric, other_metric):
        raise NotImplementedError

    def should_early_stop(self, metric):
        raise NotImplementedError

    @torch.no_grad()
    def test(self, dataloader, name='val'):
        self.model.eval()
        mean_loss = {}
        for batch_idx, batch in enumerate(
                tqdm(dataloader, total=len(dataloader), desc=name),
        ):
            batch = rec_to_gpu(batch)
            loss_dict = self._test_step(batch_idx, batch)
            mean_loss = self._add_metric(mean_loss, loss_dict)

        mean_loss = self._mean_metrics(mean_loss)
        if self.verbose:
            wandb.log({name: mean_loss})

        return mean_loss


class THSWADTrainer(BaseTrainer):
    def __init__(self, margin, norm_lambda, clipping_max_value, model_target, kg_lambda, metric_tolerance, eraly_stopping, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kg_lambda = kg_lambda
        self.model_target = model_target
        self.clipping_max_value = clipping_max_value
        self.norm_lambda = norm_lambda
        self.margin = margin

        self.prev_metric = {}
        self.cnt_no_change_metric = 0
        self.metric_tolerance = metric_tolerance
        self.eraly_stopping = eraly_stopping
        self._reset_loss()

    def _reset_loss(self):
        self.rec_total_loss = 0.
        self.kg_total_loss = 0.
        self.rec_total_cnt = 0
        self.kg_total_cnt = 0

    def _make_negative_rating(self, next_items):
        return to_gpu(torch.randint(0, len(self.model.item2entity), (len(next_items),)))

    def _make_negative_triple(self, heads, tails):
        mask = torch.rand(len(heads)) > .5
        heads[mask] = to_gpu(torch.randint(0, len(self.model.entity2id), (len(heads[mask]),)))
        tails[~mask] = to_gpu(torch.randint(0, len(self.model.entity2id), (len(tails[~mask]),)))
        return heads, tails

    def _step_rec(self, batch):
        assert batch['is_rec']
        prevs, next_items = batch['ratings']
        neg_items = self._make_negative_rating(next_items)

        # Run model. output: batch_size * cand_num, input: ratings, triples, is_rec=True
        pos_score = self.model((prevs, next_items), None, is_rec=True)
        neg_score = self.model((prevs, neg_items), None, is_rec=True)

        # Calculate loss.
        losses = loss.bpr_loss(pos_score, neg_score, target=self.model_target)
        losses += loss.orthogonal_loss(self.model.pref_embeddings.weight, self.model.pref_norm_embeddings.weight)
        return losses

    def _train_step(self, batch_idx, batch):
        if batch['is_rec']:
            losses = self._step_rec(batch)
        else:
            # kg train
            h, r, t = batch['triplets']
            nh, nt = self._make_negative_triple(h, t)

            # Run model. output: batch_size * cand_nu, input: ratings, triples, is_rec=True
            pos_score = self.model(None, (h, r, t), is_rec=False)
            neg_score = self.model(None, (nh, r, nt), is_rec=False)

            # Calculate loss.
            losses = loss.margin_loss()(pos_score, neg_score, self.margin)

            ent_embeddings = self.model.ent_embeddings(torch.cat([h, t, nh, nt]))
            rel_embeddings = self.model.rel_embeddings(r) * 2
            norm_embeddings = self.model.norm_embeddings(r) * 2
            losses += loss.orthogonal_loss(rel_embeddings, norm_embeddings)

            losses = losses + self.norm_lambda * (loss.norm_loss(ent_embeddings) + loss.norm_loss(rel_embeddings))
            losses = self.kg_lambda * losses

        # Backward pass.
        losses.backward()

        # Hard Gradient Clipping
        nn.utils.clip_grad_norm_([param for name, param in self.model.named_parameters()], self.clipping_max_value)

        if batch['is_rec']:
            self.rec_total_loss += losses.item()
            self.rec_total_cnt += 1
        else:
            self.kg_total_loss += losses.item()
            self.kg_total_cnt += 1
        return {
            'rec_total_loss': self.rec_total_loss / max(self.rec_total_cnt, 1),
            'kg_total_loss': self.kg_total_loss / max(self.kg_total_cnt, 1),
        }

    def is_first_metric_better(self, metric, other_metric):
        if 'map@10' not in metric:
            return False
        if 'map@10' not in other_metric:
            return True

        return metric['map@10'] > other_metric['map@10']

    def should_early_stop(self, metric):
        if not self.prev_metric:
            self.prev_metric = metric
            return False

        for key, value in metric.items():
            if value > self.metric_tolerance + self.prev_metric[key]:
                LOGGER.info(f'Metric {key} has significant difference')
                self.prev_metric = metric
                self.cnt_no_change_metric = 0
                return False

        self.cnt_no_change_metric += 1
        return self.eraly_stopping <= self.cnt_no_change_metric

    def train_epoch(self, dataloader, epoch=0):
        self._reset_loss()
        super().train_epoch(dataloader, epoch)
        if self.verbose:
            wandb.log({'train': {
                'epoch': epoch,
                'rec_total_loss_final': self.rec_total_loss / max(self.rec_total_cnt, 1),
                'kg_total_loss_final': self.kg_total_loss / max(self.kg_total_cnt, 1),
            }})

    def _test_step(self, batch_idx, batch):
        if batch['is_rec']:
            prevs, next_items = batch['ratings']
            score = self.model.evaluate_rec(prevs)

            topk_idxs = torch.topk(score, 5, dim=1)[1].permute(1, 0)
            map_5_score = (topk_idxs == next_items).any(0).float().mean()

            topk_idxs = torch.topk(score, 10, dim=1)[1].permute(1, 0)
            map_10_score = (topk_idxs == next_items).any(0).float().mean()

            accuracy = (score.argmax(dim=1) == next_items).float().mean()

            # loss = self._step_rec(batch)

            return {
                'accuracy': accuracy,
                'map@5': map_5_score,
                'map@10': map_10_score,
                # 'val_loss': loss,
            }
        return {}
