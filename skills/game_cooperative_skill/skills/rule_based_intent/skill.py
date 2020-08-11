import os
import pathlib
from typing import List
import types

from utils.programy_extention import MindfulDataFileBot
from utils.programy_model import run_models, cmd_postprocessing

from utils.state import State

# configuration
STORAGE_PATH = os.getenv("STORAGE_PATH")
storage_path = pathlib.Path(STORAGE_PATH) if STORAGE_PATH else pathlib.Path(__file__).parent / "storage"

share_set_path = pathlib.Path("share_storage/sets")
category_pathes = list((storage_path).glob("./categories/*")) + list(
    pathlib.Path("share_storage").glob("./categories/*")
)
aiml_files = {
    category_path.name: {"aiml": [category_path], "sets": [share_set_path]} for category_path in category_pathes
}
# init models
# {model_name: print(files) for model_name, files in aiml_files.items()}
models = {model_name: MindfulDataFileBot(files) for model_name, files in aiml_files.items()}

skill_attrs = types.SimpleNamespace()
skill_attrs.skill_name = pathlib.Path(__file__).parent.name
skill_attrs.modes = types.SimpleNamespace()
skill_attrs.modes.default = "default"


def run_skill(state: State, modes: List = [skill_attrs.modes.default]):
    human_utterances = state.human_utterances
    intents = run_models(models, human_utterances)
    intents = cmd_postprocessing(intents)
    intents = {state.add_intent(model_name, intent) for model_name, intent in intents.items()}
    return state
