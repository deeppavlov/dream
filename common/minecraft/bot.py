import logging

from javascript import require, On, Once, AsyncTask, once, off
import requests

from botconfig import BotSettings
from core.serializer import encode_actions, decode_actions
from core import actions


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


USERS = {}
ACTION_MAP = {
    "chat": actions.chat,
    "look_at_user": actions.look_at_user,
    "goto": actions.goto,
    "goto_cursor": actions.goto_cursor,
    "goto_user": actions.goto_user,
    "stop": actions.stop,
    "destroy_block": actions.destroy_block,
    "destroy_and_grab_block": actions.destroy_and_grab_block,
    "place_block": actions.place_block,
}

bot_settings = BotSettings()
mineflayer = require("mineflayer")
pathfinder = require("mineflayer-pathfinder")
collectblock = require("mineflayer-collectblock")


bot = mineflayer.createBot(
    {
        "host": bot_settings.server_host,
        "port": bot_settings.server_port,
        "username": bot_settings.bot_name,
        "hideErrors": False,
    }
)

# The spawn event
once(bot, "login")
bot.chat(f"I spawned at {bot.entity.position}")
bot.loadPlugin(pathfinder.pathfinder)
bot.loadPlugin(collectblock.plugin)
mc_data = require("minecraft-data")(bot.version)
movements = pathfinder.Movements(bot, mc_data)
bot.pathfinder.setMovements(movements)
logger.info("DREAM bot is bootstrapped and ready to play!")


@On(bot, "playerJoin")
def end(event, player):
    bot.chat("Someone joined!")


@On(bot, "chat")
def on_chat(event, user, message, *args):
    if user == bot.username:
        return

    if message.startswith("!"):
        command_args = message[1:].split()
        command = command_args.pop(0)
        action_command = ACTION_MAP.get(command)

        if action_command:
            for arg_idx in range(len(command_args)):
                # try converting strings to int to correctly parse bool values like "0"
                try:
                    command_args[arg_idx] = int(command_args[arg_idx])
                except ValueError:
                    pass
            logger.debug(f"Calling {action_command} with args {command_args}")
            action_command(bot, pathfinder, user, *command_args)
        elif command == "name":
            try:
                new_user_name = command_args[0]
                USERS[user] = new_user_name
                bot.chat(f"Got it! {user} is now known as {new_user_name}")
            except IndexError:
                bot.chat(f"Say '!name NewName' to change your DREAM username")
        else:
            bot.chat(f"In-game command {command} is not recognized")
        return

    try:
        user_id = USERS.get(user, user)
        response = requests.post(
            bot_settings.agent_url, json={"user_id": user_id, "payload": message}
        )
        data = response.json()
        response_message = data["response"]

        # mock agent response
        # actions_list = [{"action": "follow", "args": [], "kwargs": {}}]
        # response_message = f"Thy will be done! #+# {encode_actions(actions_list)}"
        # end mock
    except Exception as e:
        print(e)
        response_text = "Sorry, DREAM agent is unavailable for some reason"
    else:
        response_parts = response_message.rsplit("#+#", maxsplit=1)
        response_text = response_parts[0]

        if len(response_parts) == 2:
            response_actions = decode_actions(response_parts[1])
            for action_data in response_actions:
                action_f = ACTION_MAP[action_data["action"]]
                action_f(
                    bot,
                    pathfinder,
                    user,
                    *action_data.get("args", []),
                    **action_data.get("kwargs", {}),
                )

    bot.chat(response_text)
