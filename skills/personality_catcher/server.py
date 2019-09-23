import logging
from typing import List
import time

from fastapi import FastAPI, Body
from pydantic import BaseModel
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))


CMD_NAME = "/new_persona"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

class Input_placeholders(BaseModel):
    personality: List[str] = Body(
        ...,
        example=[
            f"{CMD_NAME}\ni prefer vinyl records to any other music recording format.\ni fix airplanes for a living.\ndrive junk cars that no one else wants.\ni think if i work hard enough i can fix the world.\ni am never still."
        ],
    )


app = FastAPI()


@app.post("/personality_catcher/")
def change_personality(placeholders: Input_placeholders):
    st_time = time.time()
    response = [
        (
            f"personality has changed by command {CMD_NAME} to this text: {per.replace(CMD_NAME, '')}",
            1.0,
            [ut for ut in per.split("\n") if not (CMD_NAME in ut)],
        )
        for per in placeholders.personality
    ]
    total_time = time.time() - st_time
    logger.info(f'personality_catcher exec time: {total_time:.3f}s')
    return response
