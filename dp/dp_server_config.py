from pathlib import Path

from deeppavlov.utils import settings
from deeppavlov.core.common.file import read_json, save_json

settings_path = Path(settings.__path__[0]) / 'server_config.json'

settings = read_json(settings_path)

settings['model_defaults'] = settings.get('model_defaults', {})

settings['model_defaults']['cobot_intent_topics'] = {
    "model_endpoint": "/model",
    "model_args_names": ["sentences"]
}


settings['model_defaults']['kbqa'] = {
    "model_endpoint": "/answers",
    "model_args_names": ["sentences"]
}
settings['model_defaults']['Chitchat'] = {
    "host": "",
    "port": "",
    "model_endpoint": "/model",
    "model_args_names": ["utterances", "annotations", "u_histories", "dialogs"]
}

settings['model_defaults']['AIMLSkill'] = {
    "model_endpoint": "/aiml",
    "model_args_names": ["utterances_batch", "history_batch", "states_batch"]
}

settings['model_defaults']['RuleBasedSkillSelector'] = {
    "model_endpoint": "/selected_skills",
    "model_args_names": ["states_batch"]
}

settings['model_defaults']['ToxicClassificationModel'] = {
    "model_endpoint": "/toxicity_annotations",
    "model_args_names": ["sentences"]
}

settings['model_defaults']['SentimentClassificationModel'] = {
    "model_endpoint": "/sentiment_annotations",
    "model_args_names": ["sentences"]
}

settings['model_defaults']['EmotionClassificationModel'] = {
    "model_endpoint": "/emotion_annotations",
    "model_args_names": ["sentences"]
}

settings['model_defaults']['stop_detect'] = {
    "model_endpoint": "/stop_probs",
    "model_args_names": ["dialog"]
}

settings['model_defaults']['cobot_convers_evaluator_annotator'] = {
    "model_endpoint": "/model",
    "model_args_names": ["dialog"]
}


settings['model_defaults']['FactoidClassificationModel'] = {
    "model_endpoint": "/factoid_annotations",
    "model_args_names": ["sentences"]
}

print(settings_path)
save_json(settings, settings_path)
