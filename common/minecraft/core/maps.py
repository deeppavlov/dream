from .actions import *
import os, json
from copy import deepcopy
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

logger = logging.getLogger(__name__)

def recreate(bot,
                pathfinder,
                invoker_username,
                max_range_goal: int = 4
                ):

    try:
        with open(os.path.join("command_memory", f"{FILENAME}.json"), "r") as f:
            buffer = json.load(f)

    except OSError as e:
        logger.warn(f"to build {FILENAME} you need to save its json config")
        exit(-1234)
            
    user_entity = bot.players[invoker_username].entity
    target_block = bot.blockAtEntityCursor(user_entity)
    target_coords = (deepcopy(target_block.position.x),
                     deepcopy(target_block.position.y),
                     deepcopy(target_block.position.z))  
    
    
    target_block.position.x = target_coords[0] 
    target_block.position.y = target_coords[1] 
    target_block.position.z = target_coords[2]
    
    try:
        bot.pathfinder.setGoal(
                pathfinder.goals.GoalLookAtBlock(
                    target_block.position, bot.world, {"range": max_range_goal}
                )
            )
    except Exception as e:
        bot.chat("Ugh, something's wrong with my pathfinding. Try again?")
        logger.warning(f"{type(e)}:{e}")
        raise WrongActionException(
                "Ugh, something's wrong with my pathfinding. Try again?"
                )

    logger.info("I " + str(target_block.position))
    current_rel_height = 0
    current_rel_x = 0
    current_rel_z = 0
    for ind, command in enumerate(buffer["command_name"]):

        logger.info(command)
        if buffer["success_flag"][ind]:
            # (0, 0, 0) -> (target_coords)
            # target_block.position.x = target_coords[0] + buffer["coords"][ind][0]
            # target_block.position.z = target_coords[2] + buffer["coords"][ind][2]
            logger.info("new blok")
            if ind == 0:
                target_block.position.y = target_coords[1]
                target_block.position.x = target_coords[0]
                target_block.position.z = target_coords[2]
            
            else:
                height_diff = buffer["coords"][ind][1] - buffer["coords"][ind-1][1]
                x_diff = buffer["coords"][ind][0] - buffer["coords"][ind-1][0]
                y_diff = buffer["coords"][ind][2] - buffer["coords"][ind-1][2]
                current_rel_height += height_diff
                current_rel_x += x_diff
                current_rel_z += y_diff
                target_block.position.y = target_coords[1] + current_rel_height
                target_block.position.x = target_coords[1] + current_rel_x
                target_block.position.z = target_coords[1] + current_rel_z

            logger.info("A " + str(target_block.position))
            try:
                ACTION_MAP[command](
                                    bot,
                                    pathfinder,
                                    invoker_username,
                                    target_block  = target_block,
                                    *buffer["command_args"][ind],
                                    **buffer["command_kwargs"][ind]
                )
            except GetActionException as e:
                # bot.pathfinder.setGoal(
                #     pathfinder.goals.GoalFollow(target_block, max_range_goal), False)
                continue
               
def get_action_map():
    ACTION_MAP.update({"recreate": recreate})   
    return ACTION_MAP

