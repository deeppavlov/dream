# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from torch import nn


class ModuleProxyWrapper(nn.Module):
    """
    Wrap a DistributedDataParallel modules and forward requests for missing
    attributes to the modules wrapped by DDP (the twice-wrapped modules).
    Also forward calls to :func:`state_dict` and :func:`load_state_dict`.

    Usage::

        modules.xyz = "hello world"
        wrapped_module = DistributedDataParallel(modules, **ddp_args)
        wrapped_module = ModuleProxyWrapper(wrapped_module)
        assert wrapped_module.xyz == "hello world"
        assert wrapped_module.state_dict().keys() == modules.state_dict().keys()

    Args:
        module (nn.Module): modules to wrap
    """

    def __init__(self, module: nn.Module):
        super().__init__()
        assert hasattr(module, "modules"), \
            "ModuleProxyWrapper expects input to wrap another modules"
        self.module = module

    def __getattr__(self, name):
        """Forward missing attributes to twice-wrapped modules."""
        try:
            # defer to nn.Module's logic
            return super().__getattr__(name)
        except AttributeError:
            try:
                # forward to the once-wrapped modules
                return getattr(self.module, name)
            except AttributeError:
                # forward to the twice-wrapped modules
                return getattr(self.module.module, name)

    def state_dict(self, *args, **kwargs):
        """Forward to the twice-wrapped modules."""
        return self.module.module.state_dict(*args, **kwargs)

    def load_state_dict(self, *args, **kwargs):
        """Forward to the twice-wrapped modules."""
        return self.module.module.load_state_dict(*args, **kwargs)

    def forward(self, *args, **kwargs):
        return self.module(*args, **kwargs)
