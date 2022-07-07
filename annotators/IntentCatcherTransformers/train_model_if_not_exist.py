import os

from deeppavlov.core.commands.utils import parse_config, expand_path
from deeppavlov import train_model


CONFIG_NAME = os.environ.get("CONFIG_NAME", None)
parsed = parse_config(CONFIG_NAME)

if expand_path(parsed["metadata"]["variables"]["MODEL_PATH"]).exists():
    # model folder exists, so it is already trained
    print("Model is already trained.")
else:
    print("Model is NOT trained.\nLet's train the model!\n\n")
    model = train_model(CONFIG_NAME)
    print("Model is trained.")
