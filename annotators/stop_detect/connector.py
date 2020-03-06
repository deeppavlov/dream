#!/usr/bin/env python
import time
import asyncio
import logging
import requests
import sentry_sdk

from typing import Callable, Dict
from os import getenv


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv('SENTRY_DSN'))
STOP_DETECTOR_URL = "http://stop_detect:8056/model"
headers = {'Content-Type': 'application/json;charset=utf-8'}


class BatchConnector:
    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            stop_result = requests.request(
                url=STOP_DETECTOR_URL,
                headers=headers,
                json=payload['payload'],
                method='POST',
                timeout=1.0
            ).json()
            result = [res[0] for res in stop_result]
            total_time = time.time() - st_time
            logger.info(f'stop_detect batch connector exec time: {total_time:.3f}s')
            # In connector [result] leads to bug, so it is not inside array like on
            # conv eval and blacklist annotator
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response={"batch": result}
            ))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=e
            ))
