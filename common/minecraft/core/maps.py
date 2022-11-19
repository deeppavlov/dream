from .actions import *
import os, json

ACTION_MAP = {
    "chat": chat,
    "look_at_user": look_at_user,
    "goto": goto,
    "goto_cursor": goto_cursor,
    "goto_user": goto_user,
    "stop": stop,
    "destroy_block": destroy_block,
    "destroy_and_grab_block": destroy_and_grab_block,
    "place_block": place_block,
}
FILENAME = "commands"

def recreate(bot,
                pathfinder,
                invoker_username,
                max_range_goal: int = 4
                ):

    try:
        with open(os.path.join("command_memory", f"{FILENAME}.json"), "r") as f:
            buffer = json.load(f)

    except OSError as e:
        print(f"to build {FILENAME} you need to save its json config")
            
    user_entity = bot.players[invoker_username].entity
    target_block = bot.blockAtEntityCursor(user_entity)
    target_coords = target_block.position    
    try:
        bot.pathfinder.setGoal(
            pathfinder.goals.GoalLookAtBlock(
                target_block.position, {"range": max_range_goal}
            )
        )
    except Exception as e:
        bot.chat("Ugh, something's wrong with my pathfinding. Try again?")
        logger.warning(f"{type(e)}:{e}")
        raise WrongActionException(
                "Ugh, something's wrong with my pathfinding. Try again?"
                )


    for ind, command in enumerate(buffer["command_name"]):
        if buffer["success_flag"][ind]:
            
            target_block.position.x = target_coords.x + buffer["coords"][ind][0]
            target_block.position.y = target_coords.y + buffer["coords"][ind][1]
            target_block.position.z = target_coords.z + buffer["coords"][ind][2]
            
            ACTION_MAP[command](
                                bot,
                                pathfinder,
                                invoker_username,
                                target_block  = target_block,
                                *buffer["command_args"][ind],
                                **buffer["command_kwargs"][ind]
            )  


def get_action_map():
    ACTION_MAP.update({"recreate": recreate})   
    return ACTION_MAP

