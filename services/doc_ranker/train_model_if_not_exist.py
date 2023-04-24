import os
import nltk.data

from deeppavlov import configs, train_model
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.file import read_json


CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
DATASET_PATH = os.environ.get("DATASET_PATH", None)
ORIGINAL_FILE_PATH = os.environ.get("ORIGINAL_FILE_PATH", None)
PARAGRAPHS_AMOUNT = 10  # максимальное число наиболее релевантных параграфов
model_config = read_json(CONFIG_PATH)


def build_dataset():
    if not os.path.exists(DATASET_PATH):
        os.mkdir(DATASET_PATH)
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    with open(ORIGINAL_FILE_PATH, "r") as f:
        i = 0
        buf = ""
        data = f.read()
        data = tokenizer.tokenize(data)

        for item in data:
            buf += item
            words = buf.split(" ")
            # сохраняем буфер в файл, если в буфере больше 100 слов
            if len(words) > 100:
                i += 1
                new_f = DATASET_PATH + str(i) + ".txt"
                with open(new_f, "w") as f_out:
                    f_out.write(buf)
                buf = ""
                print(f"creating {DATASET_PATH + str(i) + '.txt'}")


if expand_path(model_config["metadata"]["variables"]["MODEL_PATH"]).exists():
    # model folder exists, so it is already trained
    print("Model is already trained.")
else:
    print("Model is NOT trained.\nLet's train the model!\n\n")
    build_dataset()
    model_config["dataset_reader"]["data_path"] = DATASET_PATH
    model_config["dataset_reader"]["dataset_format"] = "txt"
    model_config["chainer"]["pipe"][1]["top_n"] = PARAGRAPHS_AMOUNT
    ranker = train_model(model_config)
    print("Model is trained.")
