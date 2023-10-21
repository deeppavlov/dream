
from logging import getLogger
from typing import List

import numpy as np
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.common.registry import register

@register('dnnc_preparer')
class dnnc_preparer(Component):
    def __init__(self):
        self.possible_datasets = ... 
        pass
    def __call__(self, texts):
        datasets,final_texts=[],[]
        for text in texts:
            for dataset in self.possible_datasets:
                datasets.append(dataset)
                final_texts.append(text)
        return final_texts, datasets
