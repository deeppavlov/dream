from pathlib import Path

from deeppavlov.utils import settings
from deeppavlov.core.common.file import read_json, save_json

settings_path = Path(settings.__path__[0]) / 'server_config.json'

settings = read_json(settings_path)
settings['model_defaults']['Chitchat'] = {
    "host": "",
    "port": "",
    "model_endpoint": "/chitchat",
    "model_args_names": ["utterances", "annotations", "u_histories", "dialogs"]
}
save_json(settings, settings_path)
