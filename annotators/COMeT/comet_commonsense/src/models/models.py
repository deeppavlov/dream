from src.models.gpt import LMModel
import torch.nn as nn


def make_model(opt, n_vocab, n_ctx, return_acts=True, return_probs=False):
    model = LMModel(opt.net, n_vocab, n_ctx, return_acts=return_acts, return_probs=return_probs)
    return model


def multi_gpu(model, devices):
    return nn.DataParallel(model, device_ids=devices)


def load_state_dict(model, state_dict):
    try:
        model.load_state_dict(state_dict)
    except RuntimeError:
        new_state_dict = {i[len("module.") :]: j for i, j in state_dict.items()}
        model.load_state_dict(new_state_dict)
