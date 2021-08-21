from typing import Callable, Dict


class TelegramSelector:
    async def send(self, payload: Dict, callback: Callable):
        await callback(task_id=payload["task_id"], response=[payload["payload"]])
