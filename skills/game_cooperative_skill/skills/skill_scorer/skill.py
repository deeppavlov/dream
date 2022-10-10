# %%
from typing import List
import types
import pathlib

# import requests

from utils.state import State


# url = "http://0.0.0.0:8038/model"
def get_emo_scores(utterances):
    # input_data = {"sentences": [text]}
    # try:
    #     data = requests.post(url, json=input_data).json()[0][0]
    # except Exception:
    #     print(traceback.format_exc())
    scores = {
        "anger": 0.0,
        "fear": 0.0,
        "joy": 0.0,
        "disgust": 0.0,
        "neutral": 0.0,
        "sadness": 0.0,
        "surprise": 0.0,
    }
    return scores


skill_attrs = types.SimpleNamespace()
skill_attrs.skill_name = pathlib.Path(__file__).parent.name
skill_attrs.modes = types.SimpleNamespace()
skill_attrs.modes.default = "default"


def run_skill(state: State, modes: List = [skill_attrs.modes.default]):
    utterances = state.utterances
    bot_messages = state.bot_messages
    if bot_messages:
        skill_name = bot_messages[-1]["skill_name"]
        scores = get_emo_scores(utterances)
        state.add_skill_scores(skill_name=skill_name, scores=scores)
    return state
