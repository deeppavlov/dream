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

settings['model_defaults']['AIMLSkill'] = {
    "model_endpoint": "/aiml",
    "model_args_names": ["utterances_batch", "history_batch", "states_batch"]
}

settings['model_defaults']['SkillSelector'] = {
    "model_endpoint": "/skill_names",
    "model_args_names": ["states_batch"]
}

print(settings_path)
save_json(settings, settings_path)
