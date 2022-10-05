import logging
from typing import Dict

import aiohttp
from fastapi import FastAPI


ROS_FSM_SERVER = "172.17.0.1:5000"
# Please see https://stackoverflow.com/a/62002628
ROS_FSM_STATUS_ENDPOINT = f"{ROS_FSM_SERVER}/robot_status"
ROS_FSM_INTENT_ENDPOINT = f"{ROS_FSM_SERVER}/upload_intent"


logger = logging.getLogger(__name__)
app = FastAPI()


@app.post("/respond")
async def respond(body: Dict):
    logger.info(f"Received from Dream:\n{body}")

    async with aiohttp.ClientSession() as sess:
        async with sess.get(ROS_FSM_STATUS_ENDPOINT) as status_response:
            is_free = await status_response.json()["status"] == "free"

            if is_free:
                payload = body  # fix this to actually post what you need
                async with sess.post(
                    ROS_FSM_INTENT_ENDPOINT,
                    data=payload,
                ) as intent_response:
                    ros_fsm_data = await intent_response.json()
                    response = ros_fsm_data
            else:
                response = "The robot is busy at the moment. Try again later!"

    return [response]   # wrap response in a list
