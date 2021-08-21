# %%
from typing import List
import types
import pathlib
import random

from utils.state import State


skill_attrs = types.SimpleNamespace()
skill_attrs.skill_name = pathlib.Path(__file__).parent.name
skill_attrs.modes = types.SimpleNamespace()
skill_attrs.modes.intro = "intro"
skill_attrs.modes.stop = "stop"


def run_skill(state: State, modes: List = [skill_attrs.modes.intro]):
    if skill_attrs.modes.intro in modes:
        state.add_hypothesis(
            skill_name=skill_attrs.skill_name,
            # text="I like to talk about games. "
            # "We can talk about games of tops or about you or my favorite games, what do you want to talk about?",
            # "We can talk about top games, just say: tell me about the best games",
            text=random.choice(
                [
                    "Love games. Got a list of the top released games, wanna discuss it? ",
                    "You know, I love games, especially stats like top of the games released. Wanna learn more?",
                    "So, well, one of my hobbies is keeping fresh stats about the top video games. Wanna dig into it?",
                ]
            ),
            # "Say tell me about the best games",
            confidence=1.0,
        )
    elif skill_attrs.modes.stop in modes:
        state.add_hypothesis(
            skill_name=skill_attrs.skill_name,
            text="OK, I won’t continue, but if you want to talk about the best games, "
            "Say tell me about the coolest games",
            confidence=0.0,
        )
    return state
