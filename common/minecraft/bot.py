import logging

from javascript import require, On, AsyncTask, once, off
import requests

from botconfig import BotSettings
from core.serializer import encode_actions, decode_actions, CommandBuffer
from core.actions import  WrongActionException, GetActionException
from core.maps import get_action_map


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


USERS = {}
ACTION_MAP = get_action_map()

first_user = None

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
buffer =  CommandBuffer()
is_buffer = False
# actions2buffer = ["destroy_block", "place_block", "destroy_and_grab_block"]
command_index = 0
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
    global is_buffer
    global buffer
    global command_index
    global first_user
    crash_reason = ""        
    success_flag = True
    coords = []

    if user == bot.username:
        return
    
    if first_user == None:
        fisrt_user = user
    elif (first_user != None) and (user != fisrt_user):
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
        response_text = "Sorry, DREAM agent is unavailable for some reason"
    else:
        response_parts = response_message.rsplit("#+#", maxsplit=1)
        response_text = response_parts[0]

        if len(response_parts) == 2:
            response_actions = decode_actions(response_parts[1])
            for action_data in response_actions:
                try:
                    if action_data["action"] == "start_building":
                        # buffer = CommandBuffer()
                        is_buffer = True
                    
                    elif action_data["action"] == "finish_building":
                        buffer.to_json("./command_memory/commands.json")
                        file_index = str(command_index)
                        # buffer.to_json(f"./command_memory/command_{file_index}.json")
                        is_buffer = False
                        command_index += 1
                        buffer = CommandBuffer()


                    action_f = ACTION_MAP[action_data["action"]]

                    action_f(
                        bot,
                        pathfinder,
                        user,
                        *action_data.get("args", []),
                        **action_data.get("kwargs", {}),
                    )
                except WrongActionException as e:
                    crash_reason = str(e)        
                    success_flag = False
                    coords = []
                except GetActionException as e:
                    coords = [int(c) for c in str(e).split()]
                
                if (action_data["action"] == "place_block") and is_buffer:
                    buffer.append(
                        success_flag = success_flag,
                        crash_reason = crash_reason,
                        command_name = action_f.__name__,
                        command_args = action_data.get("args", []),
                        command_kwargs = action_data["kwargs"],
                        response = response_text,
                        coords = coords
                    )

    bot.chat(response_text)
