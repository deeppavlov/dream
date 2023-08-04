import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F

from src.utils.misc import to_gpu


class margin_loss(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, pos, neg, margin):
        zero_tensor = to_gpu(torch.FloatTensor(pos.size()))
        zero_tensor.zero_()
        zero_tensor = autograd.Variable(zero_tensor)
        return torch.sum(torch.max(pos - neg + margin, zero_tensor))


def orthogonal_loss(rel_embeddings, norm_embeddings):
    return torch.sum(torch.sum(norm_embeddings * rel_embeddings, dim=1, keepdim=True) ** 2 / torch.sum(rel_embeddings ** 2, dim=1, keepdim=True))


def norm_loss(embeddings, dim=1):
    norm = torch.sum(embeddings ** 2, dim=dim, keepdim=True)
    return torch.sum(torch.max(norm - to_gpu(autograd.Variable(torch.FloatTensor([1.0]))), to_gpu(autograd.Variable(torch.FloatTensor([0.0])))))


def bpr_loss(pos, neg, target=1.0):
    loss = - F.logsigmoid(target * ( pos - neg ))
    return loss.mean()
