import asyncio
from collections import defaultdict


# TODO(pugin): refactor after tasks will be introduced
class CurrentLoadStatsClass:
    def __init__(self):
        self.services_load = defaultdict(int)
        self.internal_q = asyncio.Queue()

    async def register_stats(self, service_name, val, req_type):
        if req_type == 'send':
            self.services_load[service_name] += 1
            await self.internal_q.put({service_name: self.services_load[service_name]})
        elif req_type == 'done':
            self.services_load[service_name] -= 1
            await self.internal_q.put({service_name: self.services_load[service_name]})

    def show_stats(self):
        return self.services_load

    async def work_with_ws(self, ws):
        while True:
            if self.internal_q.qsize():
                item = await self.internal_q.get()
                await ws.send_json(item)
            await asyncio.sleep(0.1)
