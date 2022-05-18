from javascript import require, On, Once, AsyncTask, once, off
import requests

from botconfig import BotSettings
from core.serializer import encode_actions, decode_actions
from core import actions


USERS = {}
ACTION_MAP = {"goto": actions.goto}

bot_settings = BotSettings()
mineflayer = require("mineflayer")
pathfinder = require("mineflayer-pathfinder")

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
mc_data = require("minecraft-data")(bot.version)
movements = pathfinder.Movements(bot, mc_data)
bot.pathfinder.setMovements(movements)


@On(bot, "playerJoin")
def end(event, player):
    bot.chat("Someone joined!")


@On(bot, "chat")
def on_chat(event, user, message, *args):
    if user == bot.username:
        return

    if message.startswith("!name"):
        try:
            command, new_user_name = message.split(" ")
            USERS[user] = new_user_name
            bot.chat(f"Got it! {user} is now known as {new_user_name}")
        except ValueError:
            bot.chat(f"Say '!name NewName' to change your DREAM username")
        return

    try:
        user_id = USERS.get(user, user)
        response = requests.post(bot_settings.agent_url, json={"user_id": user_id, "payload": message})
        data = response.json()

        # mock agent response
        # actions_list = [{"action": "goto", "args": [10, 10, 2], "kwargs": {"range_goal": 1}}]
        # response_message = f"Thy will be done! #+# {encode_actions(actions_list)}"
        # end mock
        response_message = data["response"]
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
                action_f(bot, pathfinder, *action_data["args"], **action_data["kwargs"])

    bot.chat(response_text)

    # If the message contains stop, remove the event listener and stop logging.
    # if 'stop' in message:
    #     off(bot, 'chat', on_chat)
