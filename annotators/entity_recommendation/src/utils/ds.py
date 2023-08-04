import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np


def greater_strategy(x, gt=5):
    if x > gt:
        return True, 0
    return False, x + 1


def load_wiki_dataset(filename, graph=None, verbose_remove=False):
    triplets = []
    cnt_removed = 0
    with open(filename, 'r') as f:
        for i, line in enumerate(f):
            triplets.append([x for x in line.split()])
            assert (
                len(triplets[-1]) == 3
            ), f'Line {i} in {filename} is not a valid triple: {line}'
            if graph is not None:
                try:
                    triplets[-1][0] = graph.entity2id[triplets[-1][0]]
                    triplets[-1][1] = graph.relation2id[triplets[-1][1]]
                    triplets[-1][2] = graph.entity2id[triplets[-1][2]]
                except KeyError:
                    cnt_removed += 1
                    v = triplets.pop()
                    if verbose_remove:
                        print(v, 'was removed')

    if cnt_removed > 0:
        print(f'{cnt_removed} triplets were removed from {filename}')

    return triplets


def select_last_entities(dialog, cnt_entities, pad_item):
    entities = []
    for message in reversed(dialog):
        if not message:
            continue

        for entity in message:
            entities += [entity]
            if len(entities) == cnt_entities:
                return entities

    entities = [pad_item] * (cnt_entities - len(entities)) + entities
    return entities


class DialogDataset(Dataset):
    def __init__(self, dialogs, pad_item, prev_count=3, item2id=None):
        super().__init__()
        self.data = []
        self.targets = []
        for j, messages in enumerate(dialogs):
            for i in range(len(messages)):
                if not messages[i]:
                    continue

                prev = select_last_entities(messages[:i], prev_count, pad_item)
                if np.all(np.array(prev) == pad_item):
                    continue

                if item2id is not None:
                    for k in range(len(prev)):
                        prev[k] = item2id.get(prev[k], pad_item)
                prev = np.array(prev)

                for tgt in messages[i]:
                    if item2id is not None:
                        tgt = item2id.get(tgt, pad_item)
                    if tgt == pad_item:
                        continue

                    self.data.append(prev)
                    self.targets.append(tgt)
                    prev = np.append(prev[1:], tgt)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index], self.targets[index]


class TSHWADItarator(object):
    TRIPLETS = 'triplets'
    DIALOG = 'dialog'

    def __init__(
            self,
            triplets_loader: DataLoader,
            dialog_loader: DataLoader,
            switch_strategy=greater_strategy,
    ):
        self.triplets_loader = triplets_loader
        self.dialog_loader = dialog_loader
        self.triplets_iter = iter(triplets_loader)
        self.dialog_iter = iter(dialog_loader)
        self.switch_strategy = switch_strategy
        self.step = 0
        self.triplets_stopped = False
        self.dialog_stopped = False
        self.current_loader = self.TRIPLETS

    def _switch_if_needed(self):
        has_to_switch, self.step = self.switch_strategy(self.step)
        if has_to_switch:
            self.current_loader = (
                self.DIALOG
                if self.current_loader == self.TRIPLETS
                else self.TRIPLETS
            )

    def __next__(self):
        self._switch_if_needed()
        if self.current_loader == self.TRIPLETS:
            try:
                return {'is_rec': False, 'triplets': next(self.triplets_iter)}
            except StopIteration:
                if self.dialog_stopped:
                    raise

                self.triplets_stopped = True
                self.triplets_iter = iter(self.triplets_loader)
                return next(self)

        try:
            return {'is_rec': True, 'ratings': next(self.dialog_iter)}
        except StopIteration:
            if self.triplets_stopped:
                raise

            self.dialog_stopped = True
            self.dialog_iter = iter(self.dialog_loader)
            return next(self)


class TSHWADLoader:
    def __init__(
            self,
            triplets_loader,
            dialog_loader,
            switch_strategy=greater_strategy,
    ):
        self.triplets_loader = triplets_loader
        self.dialog_loader = dialog_loader
        self.switch_strategy = switch_strategy

    def __iter__(self):
        return TSHWADItarator(
            self.triplets_loader, self.dialog_loader, self.switch_strategy,
        )

    def __len__(self):
        """
        Returns approximate length of the loader
        """
        return (
            max(len(self.triplets_loader), len(self.dialog_loader)) * 2
            - max(
                self.triplets_loader.batch_size, self.dialog_loader.batch_size,
            )
        )
