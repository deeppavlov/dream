import json
import asyncio
from aiohttp import web

result = []
got_messages = 0

class TestPoller:
    async def handle_updates(self, request: web.Request):
        global result
        if request.method == 'GET':
            res = result
            result = []
            return web.json_response({'result': res})
        elif request.method == 'POST':
            data = await request.json()
            result.append(data)
            return web.Response(status=200)


    async def handle_message(self, request: web.Request):
        global got_messages, event
        if request.method == 'POST':
            got_messages -= 1
            if got_messages == 0:
                event.set()
            return web.Response(status=200)


    async def test_set_value(self, aiohttp_server, aiohttp_client):
        app = web.Application()
        app.add_routes([web.get('/bot{token}/getUpdates', self.handle_updates),
                        web.post('/bot{token}/getUpdates', self.handle_updates),
                        web.get('/bot{token}/sendMessage', self.handle_message),
                        web.post('/bot{token}/sendMessage', self.handle_message)])
        server = await aiohttp_server(app, port=6666)
        client = await aiohttp_client(server)
        global result, event, got_messages
        event = asyncio.Event()
        got_messages = 200
        result = [{'message': {'text': 'No work and play makes Jack a dull boy.', 'chat': {'id': i}}} for i in range(200)]
        #for _ in range(200):
        #    resp = await client.post('/bot{asd}/getUpdates', data=json.dumps({'message': {'text': 'No work and play makes Jack a dull boy.', 'chat': {'id': 42}}}))
        #assert resp.status == 200
        await event.wait()
