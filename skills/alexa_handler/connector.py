#!/usr/bin/env python
import time
import asyncio
import logging
from typing import Callable, Dict
import sentry_sdk
from os import getenv


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))


class AlexaHandlerConnector:
    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            text = payload["payload"]["sentences"][0]
            assert "/alexa_" in text

            cands = ["alexa handler: command logged"]
            confs = [1.0]
            attrs = [{}]

            total_time = time.time() - st_time
            logger.info(f"alexa_handler_skill exec time: {total_time:.3f}s")
            asyncio.create_task(callback(task_id=payload["task_id"], response=[cands, confs, attrs]))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=e))
