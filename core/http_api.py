import asyncio

from aiohttp import web
from string import hexdigits
from datetime import datetime
from state_formatters.output_formatters import (http_api_output_formatter,
                                                http_debug_output_formatter)


async def init_app(agent, session, consumers, debug=False):
    app = web.Application()
    handler = ApiHandler(debug)
    consumers = [asyncio.ensure_future(i.call_service(agent.process)) for i in consumers]

    async def on_startup(app):
        app['consumers'] = consumers
        app['agent'] = agent
        app['client_session'] = session

    async def on_shutdown(app):
        await app['client_session'].close()

    app.router.add_post('/', handler.handle_api_request)
    app.router.add_get('/dialogs/{dialog_id}', handler.dialog)

    app.router.add_get('/ping', handler.pong)
    app.router.add_get('/user/{user_telegram_id}', handler.dialogs_by_user)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


def prepare_startup(consumers, agent, session):
    result = []
    for i in consumers:
        result.append(asyncio.ensure_future(i.call_service(agent.process)))

    async def startup_background_tasks(app):
        app['consumers'] = result
        app['agent'] = agent
        app['client_session'] = session

    return startup_background_tasks


async def on_shutdown(app):
    await app['client_session'].close()


class ApiHandler:
    def __init__(self, debug=False):
        self.debug = debug

    async def handle_api_request(self, request):
        async def handle_command(payload, user_id, state_manager):
            if payload in {'/start', '/close'} and state_manager:
                await state_manager.drop_active_dialog(user_id)
                return True

        response = {}
        register_msg = request.app['agent'].register_msg
        if request.method == 'POST':
            if request.headers.get('content-type') != 'application/json':
                raise web.HTTPBadRequest(reason='Content-Type should be application/json')
            data = await request.json()
            user_id = data.pop('user_id')
            payload = data.pop('payload', '')

            if not user_id:
                raise web.HTTPBadRequest(reason='user_id key is required')
            command_performed = await handle_command(payload, user_id, request.app['agent'].state_manager)
            if command_performed:
                return web.json_response({'user_id': user_id, 'response': 'command_performed'})

            response = await register_msg(utterance=payload, user_telegram_id=user_id,
                                          user_device_type=data.pop('user_device_type', 'http'),
                                          date_time=datetime.now(),
                                          location=data.pop('location', ''),
                                          channel_type='http_client',
                                          message_attrs=data, require_response=True)

            if response is None:
                raise RuntimeError('Got None instead of a bot response.')
            if self.debug:
                return web.json_response(http_debug_output_formatter(response['dialog'].to_dict()))
            else:
                return web.json_response(http_api_output_formatter(response['dialog'].to_dict()))

    async def dialog(self, request):
        state_manager = request.app['agent'].state_manager
        dialog_id = request.match_info['dialog_id']
        if len(dialog_id) == 24 and all(c in hexdigits for c in dialog_id):
            dialog_obj = await state_manager.get_dialog_by_id(dialog_id)
            if not dialog_obj:
                raise web.HTTPNotFound(reason=f'dialog with id {dialog_id} does not exist')
            return web.json_response(dialog_obj.to_dict())
        raise web.HTTPBadRequest(reason='dialog id should be 24-character hex string')

    async def pong(self, request):
        return web.json_response("pong")

    async def dialogs_by_user(self, request):
        state_manager = request.app['agent'].state_manager
        user_telegram_id = request.match_info['user_telegram_id']
        dialogs = await state_manager.get_dialogs_by_user_ext_id(user_telegram_id)
        return web.json_response([i.to_dict() for i in dialogs])
