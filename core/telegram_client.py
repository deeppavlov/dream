import asyncio

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor


class TelegramMessageProcessor:
    def __init__(self, register_msg):
        self.register_msg = register_msg

    async def handle_message(self, message):
        response = await self.register_msg(
            utterance=message.text,
            user_telegram_id=str(message.from_user.id),
            user_device_type='telegram',
            date_time=message.date, location='', channel_type='telegram',
            require_response=True
        )
        await message.answer(response['dialog']['utterances'][-1]['text'])


def run_tg(token, proxy, agent):
    loop = asyncio.get_event_loop()
    bot = Bot(token=token, loop=loop, proxy=proxy)
    dp = Dispatcher(bot)
    tg_msg_processor = TelegramMessageProcessor(agent.register_msg)

    dp.message_handler()(tg_msg_processor.handle_message)

    executor.start_polling(dp, skip_updates=True)
