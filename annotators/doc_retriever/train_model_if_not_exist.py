import os

from deeppavlov import train_model
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.file import read_json
from common.build_dataset import build_dataset


CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
DATASET_PATH = os.environ.get("DATASET_PATH", None)
ORIGINAL_FILE_PATH = os.environ.get("ORIGINAL_FILE_PATH", None)
PARAGRAPHS_NUM = 5  # максимальное число наиболее релевантных параграфов

model_config = read_json(CONFIG_PATH)
if expand_path(model_config["metadata"]["variables"]["MODELS_PATH"]).exists():  # заменила с MODEL_PATH
    # model folder exists, so it is already trained
    print("Model is already trained.")
else:
    print("Model is NOT trained.\nLet's train the model!\n\n")
    build_dataset(DATASET_PATH, ORIGINAL_FILE_PATH)
    model_config["dataset_reader"]["data_path"] = DATASET_PATH
    model_config["dataset_reader"]["dataset_format"] = "txt"
    model_config["chainer"]["pipe"][1]["top_n"] = PARAGRAPHS_NUM
    ranker = train_model(model_config)
    print("Model is trained.")
