from torch.optim.lr_scheduler import LambdaLR


def get_epoch_lr(opt, steps_in_epochs, max_epochs=100, start_value=1e-2, min_value=1e-8) -> LambdaLR:
    epoch_step_size = (start_value - min_value) / max_epochs
    func = lambda step: start_value - (epoch_step_size * min(step // steps_in_epochs, max_epochs))
    return LambdaLR(opt, func)
