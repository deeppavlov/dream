import asyncio
from aiohttp import web


result = []

async def handle_updates(request: web.Request):
    global result
    if request.method == 'GET':
        res = result
        result = []
        return web.json_response({'result': res})
    elif request.method == 'POST':
        data = await request.json()
        result.append(data)
        return web.Response(status=200)

async def handle_message(request: web.Request):
    if request.method == 'POST':
        data = await request.json()
        print(data)
        return web.Response(status=200)


loop = asyncio.get_event_loop()

app = web.Application(loop=loop)
app.add_routes([web.get('/bot{token}/getUpdates', handle_updates),
                web.post('/bot{token}/getUpdates', handle_updates),
                web.get('/bot{token}/sendMessage', handle_message),
                web.post('/bot{token}/sendMessage', handle_message)])




if __name__ == '__main__':
    web.run_app(app, port=6666)
