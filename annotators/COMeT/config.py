from typing import Optional, Union
from pydantic import BaseSettings, validator
import os

ATOMIC_VALID_EFFECTS = {"all", "oEffect", "oReact", "oWant", "xAttr", "xEffect", "xIntent", "xNeed", "xReact", "xWant"}
CONCEPTNET_VALID_RELATIONS = {"all", "AtLocation", "CapableOf", "Causes", "CausesDesire", "CreatedBy", "DefinedAs",
                              "Desires", "HasA", "HasFirstSubevent", "HasLastSubevent", "HasPrerequisite",
                              "HasProperty", "HasSubevent", "IsA", "MadeOf", "MotivatedByGoal", "PartOf",
                              "ReceivesAction", "SymbolOf", "UsedFor"}
PRETRAINED_MODEL_PATH_FOLDER = "pretrained_models"


class AppConfig(BaseSettings):
    SERVICE_NAME: str
    SERVICE_PORT: int
    SENTRY_DSN: Optional[str] = None
    RANDOM_SEED: Optional[int] = 2718  # Magic number!

    GRAPH: str
    PRETRAINED_MODEL: str
    DECODING_ALGO: str

    CUDA_VISIBLE_DEVICES: Union[int, str] = "cpu"

    @validator("PRETRAINED_MODEL")
    def create_full_model_path(cls, pretrained_model_pkl):
        model_file = os.path.split(pretrained_model_pkl)[1]
        return os.path.join(PRETRAINED_MODEL_PATH_FOLDER, model_file)


settings = AppConfig()
