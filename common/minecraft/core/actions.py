# -*- coding: utf-8 -*-
"""Includes possible actions for the minecraft bot

Every function must accept ``bot`` and ``pathfinder`` as the first two arguments,
and other ``args``/``kwargs`` as needed
"""
import logging
from math import pi

from javascript import AsyncTask, Once, require


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


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

    bot.chat(text)


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
    bot.pathfinder.setGoal(pathfinder.goals.GoalNear(x, y, z, range_goal))


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
    bot.pathfinder.setGoal(pathfinder.goals.GoalFollow(user_entity, range_goal), follow)


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


def destroy_block(bot, pathfinder, invoker_username, tool=None):
    """Destroys the block which is targeted by the player

    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        tool: which tool to use

    Returns:

    """
    user_entity = bot.players[invoker_username].entity
    target_block = bot.blockAtEntityCursor(user_entity)

    if not target_block:
        bot.chat(f"{invoker_username} is not looking at any block")
        return

    logger.debug(f"User: {user_entity}")
    logger.debug(f"Target block: {target_block}")

    bot.pathfinder.setGoal(
        pathfinder.goals.GoalLookAtBlock(target_block.position, bot.world)
    )

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
            except Exception as e:
                bot.chat(f"Couldn't finish digging because {e}")
                logger.warning(f"Couldn't finish digging because {e}")
        else:
            bot.chat(f"Can't break '{target_block.name}' at {target_block.position}!")


def place_block(
    bot,
    pathfinder,
    invoker_username,
    max_range_goal: int = 4,
    face_vector: tuple = (0, 1, 0),
):
    """Places a block adjacent to the block which is targeted by the player

    Args:
        bot: bot instance
        pathfinder: pathfinder module instance
        invoker_username: minecraft user who invoked this action
        max_range_goal: max number of blocks away from the goal
        face_vector: (x, y, z) coordinates of the placed block relative to the reference block,
            e.g. the user targets (10, 10, 10), the face vector is (0, 1, 0),
            then the new block will be placed at (10, 11, 10)

    Returns:

    """
    vec3 = require("vec3").Vec3
    user_entity = bot.players[invoker_username].entity
    target_block = bot.blockAtEntityCursor(user_entity)

    if not target_block:
        bot.chat(f"{invoker_username} is not looking at any block")
        return

    # change to GoalPlaceBlock later
    bot.pathfinder.setGoal(
        pathfinder.goals.GoalLookAtBlock(
            target_block.position, bot.world, {"range": max_range_goal}
        )
    )

    @Once(bot, "goal_reached")
    def try_placing(event, state_goal):
        try:
            bot.chat(f"Placing a block near {target_block.position}")
            bot.placeBlock(target_block, vec3(*face_vector))
        except Exception as e:
            bot.chat(f"Couldn't place the block because {e}")
            logger.warning(f"Couldn't place the block because {e}")
