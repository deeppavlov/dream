import logging
import argparse
import uuid
from datetime import datetime
from string import hexdigits
from os import getenv

import asyncio
from aiohttp import web, ClientSession
from aiogram import Bot
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher

from core.agent import Agent
from core.pipeline import Pipeline
from core.service import Service
from core.connectors import EventSetOutputConnector, HttpOutputConnector
from core.config_parser import parse_old_config, get_service_gateway_config
from core.state_manager import StateManager
from state_formatters.output_formatters import http_api_output_formatter, http_debug_output_formatter

from sys import stdout
import sentry_sdk

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('service_logger')
fh = logging.FileHandler('../service.log')
logger.addHandler(fh)
logger.addHandler(logging.StreamHandler(stdout))

sentry_sdk.init(getenv('SENTRY_DSN'))
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', help='run agent in default mode or as one of the high load components',
                    default='default', choices=['default', 'agent', 'service', 'channel'])
parser.add_argument('-n', '--service-name', help='service name for service run mode', type=str)
parser.add_argument("-ch", "--channel", help="run agent in telegram, cmd_client or http_client", type=str,
                    choices=['cmd_client', 'http_client', 'telegram'], default='cmd_client')
parser.add_argument('-p', '--port', help='port for http client, default 4242', default=4242)
parser.add_argument('-d', '--debug', help='run in debug mode', action='store_true')
parser.add_argument('-rl', '--response-logger', help='run agent with services response logging', action='store_true')

args = parser.parse_args()
MODE = args.mode
CHANNEL = args.channel


def response_logger(workflow_record):
    for service_name, service_data in workflow_record['services'].items():
        done = service_data['agent_done_time']
        send = service_data['agent_send_time']
        if not send or not done:
            continue
        logger.debug(f'{service_name}\t{round(done - send, 5)}\tseconds')


def prepare_agent(services, endpoint: Service, input_serv: Service, use_response_logger: bool):
    pipeline = Pipeline(services)
    pipeline.add_responder_service(endpoint)
    pipeline.add_input_service(input_serv)
    if use_response_logger:
        response_logger_callable = response_logger
    else:
        response_logger_callable = None
    agent = Agent(pipeline, StateManager(), response_logger_callable=response_logger_callable)
    return agent.register_msg, agent.process


async def run(register_msg):
    user_id = input('Provide user id: ')
    while True:
        msg = input(f'You ({user_id}): ').strip()
        if msg:
            response = await register_msg(utterance=msg, user_telegram_id=user_id, user_device_type='cmd',
                                          location='lab', channel_type=CHANNEL,
                                          deadline_timestamp=None, require_response=True)
            print('Bot: ', response['dialog']['utterances'][-1]['text'])


class TelegramMessageProcessor:
    def __init__(self, register_msg):
        self.register_msg = register_msg

    async def handle_message(self, message):
        response = await self.register_msg(
            utterance=message.text,
            user_telegram_id=str(message.from_user.id),
            user_device_type='telegram',
            date_time=datetime.now(), location='', channel_type='telegram',
            require_response=True
        )
        await message.answer(response['dialog']['utterances'][-1]['text'])


async def on_shutdown(app):
    await app['client_session'].close()


async def init_app(register_msg, intermediate_storage,
                   on_startup, on_shutdown_func=on_shutdown,
                   debug=False):
    app = web.Application(debug=True)
    handle_func = await api_message_processor(
        register_msg, intermediate_storage, debug)
    app.router.add_post('/', handle_func)
    app.router.add_get('/dialogs', users_dialogs)
    app.router.add_get('/dialogs/{dialog_id}', dialog)
    app.router.add_get('/ping', pong)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown_func)
    return app


def prepare_startup(consumers, process_callable, session):
    result = []
    for i in consumers:
        result.append(asyncio.ensure_future(i.call_service(process_callable)))

    async def startup_background_tasks(app):
        app['consumers'] = result
        app['client_session'] = session

    return startup_background_tasks


async def api_message_processor(register_msg, intermediate_storage, debug=False):
    async def api_handle(request):
        response = None
        if request.method == 'POST':
            if request.headers.get('content-type') != 'application/json':
                raise web.HTTPBadRequest(reason='Content-Type should be application/json')
            data = await request.json()
            user_id = data.pop('user_id')
            payload = data.pop('payload', '')

            if not user_id:
                raise web.HTTPBadRequest(reason='user_id key is required')

            event = asyncio.Event()
            message_uuid = uuid.uuid3(uuid.NAMESPACE_DNS, f'{user_id}{payload}{datetime.now()}').hex
            await register_msg(utterance=payload, user_telegram_id=user_id,
                               user_device_type=data.pop('user_device_type', 'http'),
                               date_time=datetime.now(),
                               location=data.pop('location', ''),
                               channel_type=CHANNEL,
                               event=event,
                               message_uuid=message_uuid,
                               message_attrs=data)
            await event.wait()
            bot_response = intermediate_storage.pop(message_uuid)

            if bot_response is None:
                raise RuntimeError('Got None instead of a bot response.')
            if debug:
                response = http_debug_output_formatter(bot_response)
            else:
                response = http_api_output_formatter(bot_response)

        return web.json_response(response)

    return api_handle


async def users_dialogs(request):
    from core.state_schema import Dialog
    exist_dialogs = Dialog.objects()
    result = list()
    for i in exist_dialogs:
        result.append(i.to_dict())
    return web.json_response(result)


async def pong(request):
    return web.json_response("pong")


async def dialog(request):
    from core.state_schema import Dialog
    dialog_id = request.match_info['dialog_id']
    if dialog_id == 'all':
        dialogs = Dialog.objects()
        return web.json_response([i.to_dict() for i in dialogs])
    if len(dialog_id) == 24 and all(c in hexdigits for c in dialog_id):
        d = Dialog.objects(id__exact=dialog_id)
        if not d:
            raise web.HTTPNotFound(reason=f'dialog with id {dialog_id} is not exist')
        return web.json_response(d[0].to_dict())
    raise web.HTTPBadRequest(reason='dialog id should be 24-character hex string')


def run_default():
    services, workers, session, gateway = parse_old_config()

    if CHANNEL == 'cmd_client':
        endpoint = Service('cmd_responder', EventSetOutputConnector('cmd_responder').send,
                           StateManager.save_dialog_dict, 1, ['responder'])
        input_srv = Service('input', None, StateManager.add_human_utterance_simple_dict, 1, ['input'])
        loop = asyncio.get_event_loop()
        loop.set_debug(args.debug)
        register_msg, process = prepare_agent(services, endpoint, input_srv, use_response_logger=args.response_logger)
        if gateway:
            gateway.on_channel_callback = register_msg
            gateway.on_service_callback = process
        future = asyncio.ensure_future(run(register_msg))
        for i in workers:
            loop.create_task(i.call_service(process))
        try:
            loop.run_until_complete(future)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise e
        finally:
            future.cancel()
            if session:
                loop.run_until_complete(session.close())
            if gateway:
                gateway.disconnect()
            loop.stop()
            loop.close()
            logging.shutdown()
    elif CHANNEL == 'http_client':
        if not session:
            session = ClientSession()
        intermediate_storage = {}
        endpoint = Service('http_responder', HttpOutputConnector(intermediate_storage, 'http_responder').send,
                           StateManager.save_dialog_dict, 1, ['responder'])
        input_srv = Service('input', None, StateManager.add_human_utterance_simple_dict, 1, ['input'])
        register_msg, process_callable = prepare_agent(services, endpoint, input_srv, args.response_logger)
        if gateway:
            gateway.on_channel_callback = register_msg
            gateway.on_service_callback = process_callable
        app = init_app(register_msg, intermediate_storage, prepare_startup(workers, process_callable, session),
                       on_shutdown, args.debug)
        web.run_app(app, port=args.port)

    elif CHANNEL == 'telegram':
        token = getenv('TELEGRAM_TOKEN')
        proxy = getenv('TELEGRAM_PROXY')

        loop = asyncio.get_event_loop()

        bot = Bot(token=token, loop=loop, proxy=proxy)
        dp = Dispatcher(bot)
        endpoint = Service('telegram_responder', EventSetOutputConnector('telegram_responder').send,
                           StateManager.save_dialog_dict, 1, ['responder'])
        input_srv = Service('input', None, StateManager.add_human_utterance_simple_dict, 1, ['input'])
        register_msg, process = prepare_agent(
            services, endpoint, input_srv, use_response_logger=args.response_logger)
        if gateway:
            gateway.on_channel_callback = register_msg
            gateway.on_service_callback = process
        for i in workers:
            loop.create_task(i.call_service(process))
        tg_msg_processor = TelegramMessageProcessor(register_msg)

        dp.message_handler()(tg_msg_processor.handle_message)

        executor.start_polling(dp, skip_updates=True)


def run_agent():
    raise NotImplementedError


def run_service():
    from core.transport.mapping import GATEWAYS_MAP, CONNECTORS_MAP

    service_name = args.service_name
    gateway_config = get_service_gateway_config(service_name)
    service_config = gateway_config['service']

    formatter = service_config['formatter']
    connector_type = service_config['protocol']
    connector_cls = CONNECTORS_MAP[connector_type]
    connector = connector_cls(service_config=service_config, formatter=formatter)

    transport_type = gateway_config['transport']['type']
    gateway_cls = GATEWAYS_MAP[transport_type]['service']
    gateway = gateway_cls(config=gateway_config, to_service_callback=connector.send_to_service)

    loop = asyncio.get_event_loop()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        raise e
    finally:
        gateway.disconnect()
        loop.stop()
        loop.close()
        logging.shutdown()


def run_channel():
    raise NotImplementedError


def main():
    if MODE == 'default':
        run_default()
    elif MODE == 'agent':
        run_agent()
    elif MODE == 'service':
        run_service()
    elif MODE == 'channel':
        run_channel()


if __name__ == '__main__':
    main()
