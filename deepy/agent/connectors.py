#!/usr/bin/env python
import asyncio
import logging
from typing import Callable, Dict

import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {'Content-Type': 'application/json;charset=utf-8'}


class BatchConnector:
    def __init__(self, url: str):
        self._url = url

    async def send(self, payload: Dict, callback: Callable):
        emotion_result = requests.request(
            url=self._url,
            headers=headers,
            json=payload['payload'],
            method='POST'
        ).json()
        asyncio.create_task(callback(
            task_id=payload['task_id'],
            response={"batch": emotion_result}
        ))
