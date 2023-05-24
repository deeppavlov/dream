import socket

from typing import Callable


class MintConnector:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.cl_socket = socket.socket()
        self.cl_socket.connect((self.host, self.port))

        print(f"connection initiated to {self.host}:{self.port}")
        

    async def send(self, payload: dict, callback: Callable):
        msg = payload['human_utterances'][-1]['text']
        self.cl_socket.send(msg)
        try:
            recieved_bytes: bytes = 0
            while recieved_bytes == 0:                           # if we recieved 0 bytes, we probably didn't recieve anything
                recieved_bytes = self.cl_socket.recv(1024)       # make async?
            if recieved_bytes == -1:
                raise OSError("Socket handling failed.")
            response = recieved_bytes.decode()                   # "command executed", "no such command", etc.
        except Exception as e:
            response = e
        await callback(task_id=payload["task_id"], response=response)
