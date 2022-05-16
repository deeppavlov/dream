# -*- coding: utf-8 -*-
"""Includes possible actions for the minecraft bot

Every function must accept ``bot`` and ``pathfinder`` as the first two arguments,
and other ``args``/``kwargs`` as needed
"""


def goto(bot, pathfinder, x, y, z, range_goal=1):
    bot.pathfinder.setGoal(pathfinder.goals.GoalNear(x, y, z, range_goal))
