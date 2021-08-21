import argparse
import os

from zdialog.integrations import FlaskBot
from zdialog.integrations import TelegramBot
from src.skill import AlexaPrizeSkill as Skill
from src.consts import HOST, PORT

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=os.environ.get("HOST", default=HOST),
                        help="Host on which to run API")
    parser.add_argument("--port", type=int, default=os.environ.get("PORT", default=PORT),
                        help="Port on which to run API")
    parser.add_argument("--dev_tg_token", type=str, default=os.environ.get("DEV_TG_TOKEN"),
                        help="Telegram Token for Dev version. If None, run production version")
    args = parser.parse_args()

    bot = FlaskBot(skill=Skill,
                   bot_name="Skill",
                   host=args.host, port=args.port)

    if args.dev_tg_token is not None:
        bot = TelegramBot(skill=Skill, token=args.dev_tg_token)

    print(f"Staring bot '{Skill.__name__}'")
    bot.start_polling()
