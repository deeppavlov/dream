import logging
from typing import List

from fastapi import FastAPI, Body
from pydantic import BaseModel


CMD_NAME = "/new_persona"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[logging.StreamHandler()],
)


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
    response = [
        (
            f"personality has changed by command {CMD_NAME} to this text: {per.replace(CMD_NAME, '')}",
            1.0,
            [ut for ut in per.split("|") if not (CMD_NAME in ut)],
        )
        for per in placeholders.personality
    ]
    return response
