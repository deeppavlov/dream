import os
import src.data.atomic as atomic_data
import src.data.conceptnet as conceptnet_data
import torch

start_token = "<START>"
end_token = "<END>"
blank_token = "<blank>"


def load_checkpoint(filename):
    if os.path.exists(filename):
        checkpoint = torch.load(filename, map_location=lambda storage, loc: storage)
        return checkpoint
    raise FileNotFoundError("No model found at {}".format(filename))


def make_data_loader(opt, *args):
    if opt.dataset == "atomic":
        return atomic_data.GenerationDataLoader(opt, *args)
    elif opt.dataset == "conceptnet":
        return conceptnet_data.GenerationDataLoader(opt, *args)
