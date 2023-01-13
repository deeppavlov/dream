# -*- coding: utf-8 -*-
"""Includes possible actions for the minecraft bot
Every function must accept ``bot`` and ``pathfinder`` as the first two arguments,
and other ``args``/``kwargs`` as needed
"""
import logging
from math import pi
from javascript import AsyncTask, On, require
from javascript import config, proxy, events
import time

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


vec3 = require("vec3").Vec3

FACE_VECTOR_MAP = {
    0: vec3(0, -1, 0),
    1: vec3(0, 1, 0),
    2: vec3(0, 0, -1),
    3: vec3(0, 0, 1),
    4: vec3(-1, 0, 0),
    5: vec3(1, 0, 0),
}

#buffer exceptions to catch block positions and errors
class WrongActionException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class GetActionException(Exception):
    def __init__(self, position) -> None:
        def get_coordinates(position):
            return f"{position.x} {position.y} {position.z}"
        super().__init__(get_coordinates(position))

#TODO: handle missplacements
def Once(emitter, event):
    def decor(fn):
        i = hash(fn)

        def handler(*args, **kwargs):
            if config.node_emitter_patches:
                try:
                    fn(emitter, *args, **kwargs)
                except WrongActionException as e:
                    print(e)
            else:
                try:
                    fn(*args, **kwargs)
                except WrongActionException as e:
                    logger.warn(e)      

            del config.event_loop.callbacks[i]
        try:
            emitter.once(event, handler)
            config.event_loop.callbacks[i] = handler
        except Exception as e:
            raise e
            
    return decor


def chat(
    bot,
    pathfinder,
    invoker_username,
    text: str,
    nod_head: bool = False,
    shake_head: bool = False,
    animation_loops: int = 3,
):
    """Sends a regular DREAM response to chat with animated actions
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        text: message
        nod_head: do nodding animation
        shake_head: do shaking animation
        animation_loops: how many times animation is repeated,
            has no effect if both ``nod_head`` and ``shake_head`` are False
    Returns:
    """
    try:
        user_entity = bot.players[invoker_username].entity
        bot.lookAt(user_entity.position.offset(0, 1.6, 0))


        if nod_head:
            # this doesn't look great in game, maybe because of the server-side animations?
            for _ in range(animation_loops):
                bot.look(bot.entity.yaw, pi / 2.5)
                bot.look(bot.entity.yaw, -pi / 2.5)
            bot.lookAt(user_entity.position.offset(0, 1.6, 0))

        if shake_head:
            for _ in range(animation_loops):
                bot.look(bot.entity.yaw + pi / 5, bot.entity.pitch)
                bot.look(bot.entity.yaw - pi / 5, bot.entity.pitch)
            bot.lookAt(user_entity.position.offset(0, 1.6, 0))

    except Exception as e:
        raise WrongActionException(
            f"Couldn't look at you because\n{str(e)}!"
        )

    try:
        bot.chat(text)
    except Exception as e:
        raise WrongActionException(
            f"Couldn't chat with you because\n{str(e)}!"
        )


def look_at_user(bot, pathfinder, invoker_username, *args):
    """Looks at user's coordinates
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
    Returns:
    """
    try:
        user_entity = bot.players[invoker_username].entity
        bot.lookAt(user_entity.position.offset(0, 1.6, 0))
    except Exception as e:
        raise WrongActionException(
            f"Couldn't look at you because\n{str(e)}!"
        )


def goto(
    bot, pathfinder, invoker_username, x: int, y: int, z: int, range_goal: int = 1
):
    """Sends bot to coordinates, stopping when it is close enough
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        x: target x coordinate
        y: target y coordinate
        z: target z coordinate
        range_goal: assume target is reached when the bot is this many blocks close to it
    Returns:
    """
    try:
        bot.pathfinder.setGoal(pathfinder.goals.GoalNear(x, y, z, range_goal))
    except Exception as e:
        bot.chat("Ugh, something's wrong with my pathfinding. Try again?")
        logger.warning(f"{type(e)}:{e}")
        raise WrongActionException(
            f"Ugh, something's wrong with my pathfinding. Try again? Reason:\n{str(e)}!"
        )


def goto_cursor(bot, pathfinder, invoker_username, range_goal: int = 3):
    """Sends bot to the coordinates where the player is looking at
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        range_goal: assume target is reached when the bot is this many blocks close to it
    Returns:
    """
    user_entity = bot.players[invoker_username].entity
    target_block = bot.blockAtEntityCursor(user_entity)

    try:
        goal = pathfinder.goals.GoalNear(
            target_block.position.x,
            target_block.position.y,
            target_block.position.z,
            range_goal,
        )
        bot.pathfinder.setGoal(goal)
    except Exception as e:
        bot.chat("Ugh, something's wrong with my pathfinding. Try again?")
        logger.warning(f"{type(e)}:{e}")
        raise WrongActionException(
            f"Ugh, something's wrong with my pathfinding. Try again? Reason:\n{str(e)}!"
        )


def goto_user(
    bot, pathfinder, invoker_username, range_goal: int = 3, follow: bool = False
):
    """Sends bot to user's coordinates.
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        range_goal: assume target is reached when the bot is this many blocks close to it
        follow: if True, keep following the user until explicitly told to stop,
            else stop when reached the goal
    Returns:
    """
    user_entity = bot.players[invoker_username].entity

    try:
        bot.pathfinder.setGoal(
            pathfinder.goals.GoalFollow(user_entity, range_goal), follow
        )
    except Exception as e:
        bot.chat("Ugh, something's wrong with my pathfinding. Try again?")
        logger.warning(f"{type(e)}:{e}")
        raise WrongActionException(
            f"Ugh, something's wrong with my pathfinding. Try again? Reason:\n{str(e)}!"
        )


def stop(bot, pathfinder, invoker_username, force: bool = True):
    """Stop current pathfinding goals
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        force: if True, will stop immediately, else will find a safe place to stop.
            Using this flag might be unsafe for the bot character
    Returns:
    """
    if force:
        bot.pathfinder.setGoal(None)
    else:
        bot.pathfinder.stop()


def destroy_block(bot, pathfinder, invoker_username, target_block = None, *args):
    """Destroys the block which is targeted by the player
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
    Returns:
    """
    logger.state = None
    user_entity = bot.players[invoker_username].entity
    if target_block is None:
        target_block = bot.blockAtEntityCursor(user_entity)
    if not target_block:
        bot.chat(f"{invoker_username} is not looking at any block")
        raise WrongActionException(f"{invoker_username} is not looking at any block")

    # logger.debug(f"User: {user_entity}")
    # logger.debug(f"Target block: {target_block}")
    try:
        bot.pathfinder.setGoal(
            pathfinder.goals.GoalLookAtBlock(target_block.position, bot.world)
        )
    except Exception as e:
        raise WrongActionException(
                "Ugh, something's wrong with my pathfinding. Try again?")

    @Once(bot, "goal_reached")
    def start_digging(event, state_goal):
        if bot.canDigBlock(target_block):
            bot.chat(
                f"Breaking '{target_block.name}' block, "
                f"will take around {bot.digTime(target_block) // 1000} seconds"
            )
            try:

                @AsyncTask(start=True)
                def break_block(task):
                    bot.dig(target_block)

                bot.chat("Started digging!")

            except Exception as digging_e:
                bot.chat(f"Couldn't finish digging because {type(digging_e)}")
                logger.warning(f"Couldn't finish digging because {type(digging_e)}:{digging_e}")
                logger.state = "Couldn't finish digging"

        else:
            bot.chat(f"Can't break '{target_block.name}' at {target_block.position}!")
       
    raise GetActionException(target_block.position) \
          if logger.state is None else WrongActionException(logger.state)

def destroy_and_grab_block(bot, pathfinder, invoker_username, target_block = None, *args):
    user_entity = bot.players[invoker_username].entity

    none_flag =target_block is None

    if none_flag:
        target_block = bot.blockAtEntityCursor(user_entity)

    #TODO: do we need those?
    # if not none_flag:
    #     bot.pathfinder.setGoal(
    #             pathfinder.goals.GoalPlaceBlock(
    #                 target_block.position, bot.world, {"range": None}
    #             )
    #         )
    #     bot.pathfinder.setGoal(pathfinder.goals.GoalFollow(target_block, None), False)

    try:
        @AsyncTask(start=True)
        def collect_block(task):
            bot.collectBlock.collect(target_block)

        bot.chat(f"Collecting {target_block.position}")

    except Exception as e:
        bot.chat(f"Couldn't finish collecting because {type(e)}")
        logger.warning(f"Couldn't finish collecting because {e}")
        raise WrongActionException(f"Couldn't finish collecting because {e}")
    
    raise GetActionException(target_block.position)


def place_block(
    bot,
    pathfinder,
    invoker_username,
    max_range_goal: int = 4,
    target_block = None
):
    """Places a block adjacent to the block which is targeted by the player
 
    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        max_range_goal: max number of blocks away from the goal
 
    Returns:
 
    """
    user_entity = bot.players[invoker_username].entity
    none_flag = target_block is None

    if none_flag:
        target_block = bot.blockAtEntityCursor(user_entity)
    
    if not target_block:
        bot.chat(f"{invoker_username} is not looking at any block")
        raise WrongActionException(f"{invoker_username} is not looking at any block")
    
    # TODO if not bot_has_block
 
    # sometimes it is None. Why?
    logger.debug(f"bot.pathfinder module is {bot.pathfinder}")
 
    try:
        # change to GoalPlaceBlock later
        if none_flag:
            bot.pathfinder.setGoal(
                pathfinder.goals.GoalLookAtBlock(
                    target_block.position, bot.world, {"range": max_range_goal}
                )
            )
        else:
            
            try:
                bot.placeBlock(target_block, FACE_VECTOR_MAP[target_block.face])
            except Exception as placing_e:
                bot.chat(f"Couldn't place the block there")
                # q = str(target_block.position)
                # w = str(target_block.face)
                # e = str(target_block.type)
                # bot.chat(q + "###" + w + "###" + e)
                logger.warning(
                    f"Couldn't place the block because {type(placing_e)} {placing_e}"
                )


    except Exception as e:
        # bot.chat("Ugh, something's wrong with my pathfinding. Try again?" + str(target_block.position))
        bot.chat("Ugh, something's wrong with my pathfinding. Try again?")
        logger.warning(f"{type(e)}:{e}")
        raise WrongActionException(
                "Ugh, something's wrong with my pathfinding. Try again?"
                )
    
    @Once(bot, "goal_reached")
    def try_placing(event, state_goal):
        try:
            bot.chat(f"Placing a block near {target_block.position}")
            bot.placeBlock(target_block, FACE_VECTOR_MAP[target_block.face])
        except Exception as placing_e:
            bot.chat(f"Couldn't place the block there")
            # q = str(target_block.position)
            # w = str(target_block.face)
            # e = str(target_block.type)
            # bot.chat(q + "###" + w + "###" + e)
            logger.warning(
                f"Couldn't place the block because {type(placing_e)} {placing_e}"
            )

    raise GetActionException(target_block.position) 

