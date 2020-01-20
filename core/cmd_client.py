import asyncio
from aioconsole import ainput


async def message_processor(register_msg):
    user_id = await ainput('Provide user id: ')
    while True:
        msg = await ainput(f'You ({user_id}): ')
        msg = msg.strip()
        if msg:
            response = await register_msg(utterance=msg, user_telegram_id=user_id, user_device_type='cmd',
                                          location='lab', channel_type='cmd_client',
                                          deadline_timestamp=None, require_response=True)
            print('Bot: ', response['dialog'].utterances[-1].text)


def run_cmd(agent, session, workers, debug):
    loop = asyncio.get_event_loop()
    loop.set_debug(debug)
    future = asyncio.ensure_future(message_processor(agent.register_msg))
    for i in workers:
        loop.create_task(i.call_service(agent.process))
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
        loop.stop()
        loop.close()
