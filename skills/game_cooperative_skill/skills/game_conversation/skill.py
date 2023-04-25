# %%
from typing import List
import types
import pathlib
import os
import random

# import logging

# import traceback
# import random

from utils.programy_extention import MindfulDataFileBot
from utils.programy_model import run_models, cmd_postprocessing
from utils.state import State

# configuration
STORAGE_PATH = os.getenv("STORAGE_PATH")

# logger = logging.getLogger(__name__)

# load programy models
storage_path = pathlib.Path(STORAGE_PATH) if STORAGE_PATH else pathlib.Path(__file__).parent / "storage"

share_set_path = pathlib.Path("share_storage/sets")
category_pathes = list((storage_path).glob("./categories/*")) + list(
    pathlib.Path("share_storage").glob("./categories/*")
)
aiml_files = {
    category_path.name: {"aiml": [category_path], "sets": [share_set_path]} for category_path in category_pathes
}

# init models
# {model_name: print(files) for model_name, files in aiml_files.items()}
models = {model_name: MindfulDataFileBot(files) for model_name, files in aiml_files.items()}

# %%


skill_attrs = types.SimpleNamespace()
skill_attrs.skill_name = pathlib.Path(__file__).parent.name
skill_attrs.modes = types.SimpleNamespace()
skill_attrs.modes.intro = "intro"

month_d2s = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

rate_cmd2d = {
    "TEN_ANSWER": 10,
    "NINE_ANSWER": 9,
    "EIGHT_ANSWER": 8,
    "SEVEN_ANSWER": 7,
    "SIX_ANSWER": 6,
    "FIVE_ANSWER": 5,
    "FOUR_ANSWER": 4,
    "THREE_ANSWER": 3,
    "TWO_ANSWER": 2,
    "ONE_ANSWER": 1,
}


def rating2degree(rating):
    if rating <= 3:
        return "super low"
    elif rating <= 4:
        return "low"
    elif rating <= 6:
        return "mediocre"
    elif rating <= 8:
        return "high"
    else:
        return "really high"


def rating2comparative_degree(user_rating, public_rating):
    diff = user_rating - public_rating
    if diff < -3:
        return "way lower"
    elif diff < 0:
        return "lower"
    elif diff < 3:
        return "higher"
    else:
        return "way higher"


# def are_you_ask_handler(previous_handler_state, skill_state, state, true_model_names, true_cmds):
#     confidence = 1.0
#     scenario = True
#     # previous_handler_name = previous_handler_state.get("handler_name", "")
#     skill_name = skill_state.get("next_step", "")
#     skill_name = skill_state.get("next_step", "")
#     text = previous_handler_state.get("text", [])
#     proceed = False

#     if not skill_name:

#         games = state.get_content("games")
#         current_game = games[-1]

#         if current_game:
#             text += [f"Do you want to talk in more detail about {current_game.get('name_original')}?"]
#             skill_state_update = {"next_step": "are_you_ask", "current_game": current_game}
#         else:
#             scenario = False
#             text += ["Sory, i can not do that."]
#             skill_state_update = {"next_step": ""}
#         skill_state_update

#     elif skill_name == "are_you_ask":
#         if "YES_ANSWER" in true_cmds:
#             skill_state_update = {"next_step": "have_you_played"}
#             proceed = True
#         elif "NO_ANSWER" in true_cmds:
#             text += ["You can always talk to me about other popular games. What do you want to talk about?"]
#             skill_state_update = {"next_step": ""}
#             scenario = False
#         else:
#             current_game = skill_state.get("current_game", {})
#             # text += ["I can’t recognize the request, you can reformulate it."]
#             # if current_game:
#             #     text += [f"I asked if you were interested in talking about {current_game.get('name_original')}."]
#             #     text += ["For example, you can say: yes or no ."]
#             # text += [f"Or do you want to stop for now?"]
#             text += [
#                 f"I didn't get what you've just said.",
#                 f"As far as I understand we've discussed the {current_game.get('name_original', 'game')}.",
#                 f"Shall we keep talking about it?",
#                 # f"Or do you want to stop for now?",
#             ]
#             skill_state_update = {"next_step": "are_you_ask"}
#     handler_state = {}
#     handler_state["text"] = text
#     handler_state["confidence"] = confidence
#     handler_state["scenario"] = scenario
#     handler_state["handler_name"] = "are_you_ask"

#     return proceed, handler_state, skill_state_update, state


def have_you_played_handler(previous_handler_state, skill_state, state, true_model_names, true_cmds):
    confidence = 1.0
    scenario = True
    # previous_handler_name = previous_handler_state.get("handler_name", "")
    # logger.info(f"previous_handler_state = {previous_handler_state}")
    # logger.info(f"previous_handler_name = {previous_handler_name}")
    skill_name = skill_state.get("next_step", "")
    text = previous_handler_state.get("text", [])
    proceed = False
    skill_state_update = {}

    current_game = skill_state.get("current_game")
    if current_game is None:
        current_game = state.get_content("games")[-1]
        skill_state_update.update({"current_game": current_game})

    if skill_name in [""]:
        text += ["Have you played it before? "]
        skill_state_update.update({"next_step": "have_you_played"})

    elif skill_name == "have_you_played":
        game_id = str(current_game["id"])
        game_state = skill_state.get(game_id, {})
        if "YES_ANSWER" in true_cmds:
            game_state["game_is_played"] = True
            skill_state_update.update({"next_step": "do_you_like"})
            proceed = True
        elif "NO_ANSWER" in true_cmds:
            game_state["game_is_played"] = False
            skill_state_update.update({"next_step": "do_you_like"})
            proceed = True
        else:
            current_game = skill_state.get("current_game")
            text += [
                "I didn't get what you've just said.",
            ]
            if current_game:
                text += [f"I wonder if you played {current_game.get('name_original')}."]
                # text += ["For example, you can say: yes or no ."]
            text += ["do you want to continue? "]
            skill_state_update.update({"next_step": "have_you_played"})
        skill_state_update[game_id] = game_state

    handler_state = {}
    handler_state["text"] = text
    handler_state["confidence"] = confidence
    handler_state["scenario"] = scenario
    handler_state["handler_name"] = "have_you_played"

    return proceed, handler_state, skill_state_update, state


def do_you_like_handler(previous_handler_state, skill_state, state, true_model_names, true_cmds):
    confidence = 1.0
    scenario = True
    previous_handler_name = previous_handler_state.get("handler_name", "")
    skill_name = skill_state.get("next_step", "")
    text = previous_handler_state.get("text", [])
    proceed = False

    current_game = skill_state.get("current_game")
    game_id = str(current_game["id"])
    game_state = skill_state.get(game_id, {})

    if previous_handler_name in ["have_you_played"]:
        if game_state.get("game_is_played"):
            text += [
                f"So I suppose you liked {current_game.get('name_original')} right?",
                "How would you rate the desire to play it again, from 1 to 10?",
            ]
        else:
            text += [f"How would you rate the desire to play {current_game.get('name_original')} from 1 to 10? "]

        skill_state_update = {"next_step": "do_you_like"}

    elif skill_name == "do_you_like":
        rates = [rate_cmd2d[cmd] for cmd in true_cmds if cmd in rate_cmd2d]
        if rates:
            game_rate = max(rates)
            public_game_rate = current_game.get("rating", 0) * 2
            game_relative_rate_is_high = game_rate > public_game_rate
            game_rate_is_high = game_rate > 6
            game_state["game_rate"], game_state["game_relative_rate_is_high"], game_state["game_rate_is_high"] = (
                game_rate,
                game_relative_rate_is_high,
                game_rate_is_high,
            )

            text += [
                f"You gave it a {rating2degree(game_rate)} rating.",
                f"Your rating is {rating2comparative_degree(game_rate, public_game_rate)} "
                "than one given by the rest of the players.",
                f"Most of them rated it at {public_game_rate} points.",
            ]
            text += random.choice(
                [
                    [
                        "Hey sorry I've lost my computer games almanac and "
                        "I can't talk about the game details just yet.",
                        "But I promise to find it the next few days okay?",
                        "Wanna discuss the next game?",
                    ],
                    [
                        "Look I haven't read other details about games just yet.",
                        "Promise to find them in the next few days ok?",
                    ],
                    [
                        "Well.",
                        "I'd love to talk about other things but my developer forgot to add them to my memory banks.",
                        "Please forgive him, he's young and very clever. For now can we please discuss the next game?",
                    ],
                    [
                        "My bad.",
                        "My memory failed me and I can't recall anything else about the games.",
                        "Just ratings.",
                        "But I promise to fix my memory card and get back to you.",
                        "In the meanwhile, do you want to discuss the next game?",
                    ],
                ]
            )
            skill_state_update = {"next_step": ""}
            scenario = False
            skill_state_update[game_id] = game_state
        else:
            current_game = skill_state.get("current_game")
            text += ["I didn't get what you've just said."]

            if current_game:
                text += [f"I asked what rating would you give {current_game.get('name_original')}."]
                text += ["For example, you can say: one or ten  or any number from 1 to 10."]

            text += ["do you want to continue? "]
            skill_state_update = {"next_step": "do_you_like"}

    handler_state = {}
    handler_state["text"] = text
    handler_state["confidence"] = confidence
    handler_state["scenario"] = scenario
    handler_state["handler_name"] = "do_you_like"

    return proceed, handler_state, skill_state_update, state


def run_skill(state: State, modes: List = [skill_attrs.modes.intro]):
    model_results = run_models(models, state.human_utterances)
    true_model_names = cmd_postprocessing(model_results, model_name_only=True)
    true_cmds = cmd_postprocessing(model_results, cmd_only=True)

    skill_state_update = {}
    # print(f"<{skill_attrs.skill_name}> skill_state: {skill_state}")
    # print(f"<{skill_attrs.skill_name}> true_model_names: {true_model_names}")
    # print(f"<{skill_attrs.skill_name}> true_cmds: {true_cmds}")

    # handle loop
    proceed = True
    handler_state = {}
    i = 0
    while proceed:
        i += 1
        if skill_attrs.modes.intro in modes:
            skill_state = {}
            next_step = ""
        else:
            skill_state = state.get_skill_state(skill_attrs.skill_name)
            next_step = skill_state.get("next_step", "")

        # # if next_step in ["", "are_you_ask"]:

        # if next_step in ["are_you_ask"]:
        #     proceed, handler_state, skill_state_update, state = are_you_ask_handler(
        #         handler_state, skill_state, state, true_model_names, true_cmds
        #     )
        if next_step in ["", "have_you_played"]:
            proceed, handler_state, skill_state_update, state = have_you_played_handler(
                handler_state, skill_state, state, true_model_names, true_cmds
            )
        elif next_step in ["do_you_like"]:
            proceed, handler_state, skill_state_update, state = do_you_like_handler(
                handler_state, skill_state, state, true_model_names, true_cmds
            )

        state.update_skill_state(skill_attrs.skill_name, skill_state_update)
        # logger.info(f"{i}: next_step = {next_step}")
        # logger.info(skill_state_update)

    # print(f"skill_state_update = {skill_state_update}")

    text = handler_state.get("text", ["Sorry, i can not answer."])
    text = " ".join(text)
    confidence = handler_state.get("confidence", 0.0)
    scenario = handler_state.get("scenario", False)

    state.add_hypothesis(
        skill_name=skill_attrs.skill_name,
        text=text,
        confidence=confidence,
        scenario=scenario,
    )

    return state
