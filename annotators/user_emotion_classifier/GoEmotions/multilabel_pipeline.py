from typing import Union, Optional

import numpy as np
from transformers.pipelines import ArgumentHandler
from transformers import (
    Pipeline,
    PreTrainedTokenizer,
    ModelCard
)


class MultiLabelPipeline(Pipeline):
    def __init__(
            self,
            model: Union["PreTrainedModel", "TFPreTrainedModel"],
            tokenizer: PreTrainedTokenizer,
            modelcard: Optional[ModelCard] = None,
            framework: Optional[str] = None,
            task: str = "",
            args_parser: ArgumentHandler = None,
            device: int = -1,
            binary_output: bool = False,
            threshold: float = 0.3
    ):
        super().__init__(
            model=model,
            tokenizer=tokenizer,
            modelcard=modelcard,
            framework=framework,
            args_parser=args_parser,
            device=device,
            binary_output=binary_output,
            task=task
        )

        self.threshold = threshold

    def __call__(self, *args, **kwargs):
        outputs = super().__call__(*args, **kwargs)
        scores = 1 / (1 + np.exp(-outputs))  # Sigmoid
        results = []
        for item in scores:
            labels = []
            scores = []
            for idx, s in enumerate(item):
                if s > self.threshold:
                    labels.append(self.model.config.id2label[idx])
                    scores.append(s)
            results.append({"labels": labels, "scores": scores})
        return results
