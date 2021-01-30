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


class KBQAConnector:
    def __init__(self, url: str):
        self._url = url

    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            kbqa_result = []
            resp = requests.post(url=self._url, json=payload['payload'], timeout=0.5)
            if resp.status_code == 200:
                kbqa_result = resp.json()[0]
            total_time = time.time() - st_time
            logger.info(f'KBQA connector exec time: {total_time:.3f}s, result: {kbqa_result}')

            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response={"kbqa_res": kbqa_result}
            ))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=e
            ))
