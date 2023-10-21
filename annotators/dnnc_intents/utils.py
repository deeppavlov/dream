from deeppavlov.core.models.component import Component
from deeppavlov.core.common.registry import register
import json

@register("dnnc_preparer")
class dnnc_preparer(Component):
    def __init__(self):
        self.data = json.load(open("data_full.json","r"))
    def __call__(self, texts):
        datasets = data["train"] + data["oos_train"]
        return texts, datasets
