#!/usr/bin/env python
import asyncio
import logging
import socket
from os import getenv
from typing import Callable, Dict

import sentry_sdk

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))


class SocketConnector:
    def __init__(self, host: str, port: str):
        self.client_socket = socket.socket()  # instantiate
        self.client_socket.connect((host, int(port)))  # connect to the server

    async def send(self, payload: Dict, callback: Callable):
        try:
            logger.info(f'got payload: {payload}')
            self.client_socket.send(payload["payload"].encode())  # send message
            response = self.client_socket.recv(1024).decode()  # receive response
            logger.info(f'Received from server: {response}')  # show in terminal
            asyncio.create_task(callback(task_id=payload["task_id"], response=response))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=e))
