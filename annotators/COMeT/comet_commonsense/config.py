from typing import Optional, Union
from pydantic import BaseSettings, validator
import os

PRETRAINED_MODEL_PATH_FOLDER = ["comet_commonsense", "pretrained_models"]


class AppConfig(BaseSettings):
    SERVICE_NAME: str
    SERVICE_PORT: int
    SENTRY_DSN: Optional[str]

    GRAPH: str
    PRETRAINED_MODEL: str
    DECODING_ALGO: str

    CUDA_VISIBLE_DEVICES: Union[int, str]

    @validator("PRETRAINED_MODEL")
    def create_full_model_path(cls, pretrained_model_pkl):
        model_file = os.path.split(pretrained_model_pkl)[1]
        return os.path.join(*PRETRAINED_MODEL_PATH_FOLDER, model_file)

    @validator("CUDA_VISIBLE_DEVICES")
    def device_validator(cls, device):
        if isinstance(device, int):
            return device
        return "cpu"


settings = AppConfig()
