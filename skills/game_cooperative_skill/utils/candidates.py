# %%
from typing import List

import numpy as np


def softmax(x: np.array, t: float):
    e_x = np.exp((x - np.max(x)) / t)
    return e_x / e_x.sum(axis=0)


def sample_candidates(candidates: List, choice_num: int = 1, replace: bool = False, softmax_temperature: float = 1):
    choice_num = min(choice_num, len(candidates))

    confidences = [cand[1] for cand in candidates]
    choice_probs = softmax(confidences, softmax_temperature)

    one_dim_candidates = np.array(candidates)
    one_dim_indices = np.arange(len(one_dim_candidates))
    sampled_one_dim_indices = np.random.choice(one_dim_indices, choice_num, replace=replace, p=choice_probs)

    sampled_candidates = one_dim_candidates[sampled_one_dim_indices]
    return sampled_candidates.tolist()
