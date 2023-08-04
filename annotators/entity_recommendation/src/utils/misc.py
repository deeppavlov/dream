import torch


USE_CUDA = torch.cuda.is_available()

def to_gpu(var):
    if USE_CUDA:
        return var.cuda()
    return var

def projection_transh_pytorch(original, norm):
    return original - torch.sum(original * norm, dim=len(original.size())-1, keepdim=True) * norm
