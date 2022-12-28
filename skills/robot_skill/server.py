import logging
from typing import Dict

import aiohttp
from fastapi import FastAPI

import json

ROS_FSM_SERVER = "http://172.17.0.1:5000"
# Please see https://stackoverflow.com/a/62002628
ROS_FSM_STATUS_ENDPOINT = f"{ROS_FSM_SERVER}/robot_status"
ROS_FSM_INTENT_ENDPOINT = f"{ROS_FSM_SERVER}/upload_intent"


logger = logging.getLogger(__name__)
app = FastAPI()


@app.post("/respond")
async def respond(body: Dict):
    logger.error(f"Received from Dream:\n{body}")

    async with aiohttp.ClientSession() as sess:
        async with sess.get(ROS_FSM_STATUS_ENDPOINT) as status_response:
            is_free = (await status_response.json()).get("status") == "free"

            logger.error(f"Robot status: {is_free}")

            if is_free:
                payload = body  # fix this to actually post what you need
                await sess.post(ROS_FSM_INTENT_ENDPOINT, data=json.dumps(payload))
    return [body]
