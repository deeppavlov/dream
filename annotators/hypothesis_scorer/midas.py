# wget http://files.deeppavlov.ai/alexaprize_data/midas.tar.gz
# mkdir model
# tar -zvxf midas.tar.gz -C model
#
# pip install ...
# simpletransformers==0.60.6
# numpy==1.20.0
# pytorch=1.15

import numpy as np
from scipy.special import softmax
from simpletransformers.classification import ClassificationModel

model_dir = "/midas"
model = ClassificationModel(
    model_type="bert",
    model_name=model_dir,
    tokenizer_type="bert",
    use_cuda=True,
    num_labels=24,
    cuda_device=0,
    args={
        "sliding_window": True,
        "fp16": False,
        "reprocess_input_data": True,
        "use_multiprocessing": False,
        "cache_dir": "midas",
        "best_model_dir": "midas",
        "no_cache": True,
        "verbose": False,
    },
)
m = model.predict(["hi"])

label_to_act = {
    0: "statement",
    1: "back-channeling",
    2: "opinion",
    3: "pos_answer",
    4: "abandon",
    5: "appreciation",
    6: "yes_no_question",
    7: "closing",
    8: "neg_answer",
    9: "other_answers",
    10: "command",
    11: "hold",
    12: "complaint",
    13: "open_question_factual",
    14: "open_question_opinion",
    15: "comment",
    16: "nonsense",
    17: "dev_command",
    18: "correction",
    19: "opening",
    20: "clarifying_question",
    21: "uncertain",
    22: "non_compliant",
    23: "open_question_personal",
}


def predict(inputs):
    predictions, raw_outputs = model.predict(inputs)
    raw_outputs = [raw_output.astype(np.float64) for raw_output in raw_outputs]
    pred_probas = list(map(softmax, raw_outputs))
    responses = [dict(zip(label_to_act.values(), pred[0])) for pred in pred_probas]
    assert len(responses) == len(inputs)
    return responses
