import asyncio
import argparse
import uuid

from aiohttp import web
from datetime import datetime

from core.agent import AsyncAgent
from core.pipeline import Pipeline, Service, simple_workflow_formatter
from core.connectors import CmdOutputConnector, HttpOutputConnector
from core.config_parser import parse_old_config
from core.state_manager import StateManager
from core.transform_config import DEBUG


parser = argparse.ArgumentParser()
parser.add_argument("-ch", "--channel", help="run agent in telegram, cmd_client or http_client", type=str,
                    choices=['cmd_client', 'http_client'], default='cmd_client')
parser.add_argument('-p', '--port', help='port for http client, default 4242', default=4242)
args = parser.parse_args()
CHANNEL = args.channel


def prepare_agent(services, endpoint: Service):
    pipeline = Pipeline(services)
    pipeline.add_responder_service(endpoint)
    agent = AsyncAgent(pipeline, StateManager)

    return agent.register_msg, agent.process


async def run(register_msg):
    user_id = input('Provide user id: ')
    while True:
        msg = input(f'You ({user_id}): ').strip()
        if msg:
            await register_msg(msg, user_id, 'cmd', datetime.now(), 'lab', CHANNEL)


async def init_app(register_msg, intermediate_storage, on_startup, on_shutdown):
    app = web.Application(debug=True)
    handle_func = await api_message_processor(register_msg, intermediate_storage)
    app.router.add_post('/', handle_func)
    app.router.add_get('/dialogs', users_dialogs)
    app.router.add_get('/dialogs/{dialog_id}', dialog)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


def prepare_startup(consumers, process_callable, session):
    result = []
    for i in consumers:
        result.append(asyncio.ensure_future(i.call_service(process_callable)))

    async def startup_background_tasks(app):
        app['consumers'] = result
        app['client_session'] = session

    return startup_background_tasks


async def on_shutdown(app):
    await app['client_session'].close()


async def api_message_processor(register_msg, intermediate_storage):
    async def api_handle(request):
        result = {}
        if request.method == 'POST':
            if request.headers.get('content-type') != 'application/json':
                raise web.HTTPBadRequest(reason='Content-Type should be application/json')
            data = await request.json()
            user_id = data.get('user_id')
            payload = data.get('payload', '')

            if not user_id:
                raise web.HTTPBadRequest(reason='user_id key is required')

            event = asyncio.Event()
            message_uuid = uuid.uuid3(uuid.NAMESPACE_DNS, f'{user_id}{payload}{datetime.now()}').hex
            await register_msg(utterance=payload, user_telegram_id=user_id, user_device_type='http',
                               date_time=datetime.now(), location='', channel_type=CHANNEL,
                               event=event, message_uuid=message_uuid)
            await event.wait()
            bot_response = intermediate_storage.pop(message_uuid)

        return web.json_response({'user_id': user_id, 'response': bot_response})

    return api_handle


async def users_dialogs(request):
    from core.state_schema import Dialog
    exist_dialogs = Dialog.objects()
    result = list()
    for i in exist_dialogs:
        result.append(
            {'id': str(i.id), 'location': i.location, 'channel_type': i.channel_type, 'user': i.user.to_dict()})
    return web.json_response(result)


async def dialog(request):
    from core.state_schema import Dialog
    dialog_id = request.match_info['dialog_id']
    if dialog_id == 'all':
        dialogs = Dialog.objects()
        return web.json_response([i.to_dict() for i in dialogs])
    elif len(dialog_id) == 24 and all(c in hexdigits for c in dialog_id):
        dialog = Dialog.objects(id__exact=dialog_id)
        if not dialog:
            raise web.HTTPNotFound(reason=f'dialog with id {dialog_id} is not exist')
        else:
            return web.json_response(dialog[0].to_dict())
    else:
        raise web.HTTPBadRequest(reason='dialog id should be 24-character hex string')


if __name__ == '__main__':
    services, workers, session = parse_old_config()

    if CHANNEL == 'cmd_client':
        endpoint = Service('cmd_responder', CmdOutputConnector(), None, 1, ['responder'], set(), simple_workflow_formatter)
        loop = asyncio.get_event_loop()
        loop.set_debug(DEBUG)
        register_msg, process = prepare_agent(services, endpoint)
        future = asyncio.ensure_future(run(register_msg))
        for i in workers:
            loop.create_task(i.call_service(process))
        try:
            loop.run_until_complete(future)
        except Exception as e:
            raise e
        finally:
            loop.run_until_complete(asyncio.gather(session.close()))
            loop.close()
    elif CHANNEL == 'http_client':
        intermediate_storage = {}
        endpoint = Service('http_responder', HttpOutputConnector(intermediate_storage), None, 1, ['responder'])
        register_msg, process_callable = prepare_agent(services, endpoint)
        app = init_app(register_msg, intermediate_storage, prepare_startup(workers, process_callable, session), on_shutdown)

        web.run_app(app, port=args.port)
