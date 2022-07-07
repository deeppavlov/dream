# %%
from typing import Dict, Optional
import os
import copy
import pprint
import logging

import sentry_sdk

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)

MAX_HISTORY_LEN = 4

game_keys = ["id", "name_original"]


def get_game_hash(data):
    if all([key in data for key in game_keys]):
        return ":".join([f"{key}:{data[key]}" for key in game_keys])


def get_game_by_hash(hash, games):
    try:
        hash_segments = hash.split(":")
        if len(hash_segments) > 2 and hash_segments[0] == "id":
            return games[hash]
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        logger.exception(exc)
        games = list(games.values())
        alt_game = games[0] if games else {}
        return alt_game


def serialize_games(data):
    if isinstance(data, list):
        return [serialize_games(i) for i in data]
    elif isinstance(data, dict):
        game_hash = get_game_hash(data)
        if game_hash is not None:
            return game_hash
        else:
            return {key: serialize_games(val) for key, val in data.items()}
    else:
        return data


def deserialize_games(data, games):
    if isinstance(data, list):
        return [deserialize_games(i, games) for i in data]
    elif isinstance(data, dict):
        return {key: deserialize_games(val, games) for key, val in data.items()}
    elif isinstance(data, str):
        game = get_game_by_hash(data, games)
        if game:
            return game
        else:
            return data
    else:
        return data


class State:
    def __init__(self, games: Dict, state: Optional[Dict] = None):
        if not state:
            self.state = {
                "content_state": {},  # {content_type_str: [content_1_dict, content_2_dict, ...], ...}
                "skill_scores": {},  # {skill_name_str: [scores_1_dict, scores_2_dict, ...], ...}
                "skill_states": {},  # {skill_name_1_str: skill_state_1_dict, ...}
                "messages": [],
                "hypotheses": [],
                "intents": {},
                "policy_state": {"current_scenario_skill": "", "interrupted_scenario_stack": [], "st2": {}},
            }
        else:
            self.state = deserialize_games(state, games)
        self.state["hypotheses"] = []
        self.state["intents"] = {}

    def get_skill_state(self, skill_name: str):
        return self.state["skill_states"].get(skill_name, {})

    def update_st2_policy(self, policy: Dict):
        self.state["policy_state"]["st2"].update(policy)

    def reset_st2_policy(self):
        self.state["policy_state"]["st2"] = {}

    def update_skill_state(self, skill_name: str, skill_state: Dict):
        if skill_name in self.state["skill_states"]:
            self.state["skill_states"][skill_name].update(skill_state)
        else:
            self.state["skill_states"][skill_name] = skill_state

    def get_content(self, content_name: str, **kwargs):
        return self.state["content_state"].get(content_name, [])

    def add_content(self, content_name: str, content: Dict, **kwargs):
        self.state["content_state"][content_name] = self.state["content_state"].get(content_name, []) + [content]

    def add_skill_scores(self, skill_name: str, scores: Dict, **kwargs):
        scores = copy.deepcopy(scores)
        scores.update(kwargs)
        self.state["skill_scores"][skill_name] = self.state["skill_scores"].get(skill_name, []) + [scores]

    def add_message(self, msg):
        self.state["messages"].append(msg)
        if len(self.state["messages"]) > MAX_HISTORY_LEN:
            self.state["messages"].pop(0)

    def add_human_message(self, text: str, **kwargs):
        msg = {"user_type": "human", "text": text}
        msg.update(kwargs)
        self.add_message(msg)

    def add_bot_message(self, skill_name: str, text: str, confidence: float, scenario: bool = False, **kwargs):
        msg = {"user_type": "bot", "skill_name": skill_name, "text": text, "confidence": confidence}
        self.state["policy_state"]["current_scenario_skill"] = skill_name if scenario else ""
        msg.update(kwargs)
        self.add_message(msg)

    def add_hypothesis(self, skill_name: str, text: str, confidence: float, scenario: bool = False, **kwargs):
        hypothesis = {
            "skill_name": skill_name,
            "text": text,
            "confidence": confidence,
            "scenario": scenario,
        }
        hypothesis.update(kwargs)
        self.state["hypotheses"].append(hypothesis)

    def add_intent(self, intent_model_name: str, intent: Dict, **kwargs):
        intent = copy.deepcopy(intent)
        intent.update(kwargs)
        self.state["intents"][intent_model_name] = intent

    def interrupt_scenario(self):
        if self.current_scenario_skill:
            self.state["policy_state"]["interrupted_scenario_stack"].append(self.current_scenario_skill)

    def to_dict(self):
        return dict(serialize_games(self.state))

    def __repr__(self):
        return pprint.pformat(self.to_dict())

    @property
    def content_state(self):
        return self.state["content_state"]

    @property
    def skill_stats(self):
        return self.state["skill_stats"]

    @property
    def skill_states(self):
        return self.state["skill_states"]

    @property
    def utterances(self):
        return [msg["text"] for msg in self.state["messages"]]

    @property
    def human_utterances(self):
        return [msg["text"] for msg in self.state["messages"] if msg["user_type"] == "human"]

    @property
    def bot_utterances(self):
        return [msg["text"] for msg in self.state["messages"] if msg["user_type"] == "bot"]

    @property
    def skill_history(self):
        return [msg.get("skill_name", "") for msg in self.state["messages"] if msg["user_type"] == "bot"]

    @property
    def messages(self):
        return self.state["messages"]

    @property
    def human_messages(self):
        return [msg for msg in self.state["messages"] if msg["user_type"] == "human"]

    @property
    def bot_messages(self):
        return [msg for msg in self.state["messages"] if msg["user_type"] == "bot"]

    @property
    def hypotheses(self):
        return self.state["hypotheses"]

    @property
    def intents(self):
        return self.state["intents"]

    @property
    def current_scenario_skill(self):
        return self.state["policy_state"]["current_scenario_skill"]

    @property
    def interrupted_scenario_stack(self):
        return self.state["policy_state"]["interrupted_scenario_stack"]

    @property
    def st2_policy(self):
        return self.state["policy_state"]["st2"]
