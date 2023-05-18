from deeppavlov import build_model, train_model
from deeppavlov.core.common.file import read_json, find_config

model_config = read_json("../train_model/emotion_classifier_light.json")
# model = build_model(model_config, install=True, download=True)
model = train_model(model_config)

print(model(["You are kind of stupid", "You are a wonderful person!"]))

model.save()
