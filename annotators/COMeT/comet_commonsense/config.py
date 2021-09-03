from typing import Optional, Union
from pydantic import BaseSettings, validator
import os

PRETRAINED_MODEL_PATH_FOLDER = ["comet_commonsense", "pretrained_models"]


class AppConfig(BaseSettings):
    SERVICE_NAME: str = 'atomic'
    SERVICE_PORT: int = 8053
    SENTRY_DSN: Optional[str] = None
    RANDOM_SEED: Optional[int] = 2718  # Magic number!

    GRAPH: str = 'atomic'
    PRETRAINED_MODEL: str = 'atomic_pretrained_model.pickle'
    DECODING_ALGO: str = 'beam-3'

    CUDA_VISIBLE_DEVICES: Union[int, str] = "cpu"

    @validator("PRETRAINED_MODEL")
    def create_full_model_path(cls, pretrained_model_pkl):
        model_file = os.path.split(pretrained_model_pkl)[1]
        return os.path.join(*PRETRAINED_MODEL_PATH_FOLDER, model_file)


settings = AppConfig()
