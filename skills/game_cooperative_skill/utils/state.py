# %%
from typing import Dict, Optional
import copy
import pprint


class State:
    def __init__(self, state: Optional[Dict] = None):
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
            self.state = state
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

    def add_human_message(self, text: str, **kwargs):
        msg = {"user_type": "human", "text": text}
        msg.update(kwargs)
        self.state["messages"].append(msg)

    def add_bot_message(self, skill_name: str, text: str, confidence: float, scenario: bool = False, **kwargs):
        msg = {"user_type": "bot", "skill_name": skill_name, "text": text, "confidence": confidence}
        self.state["policy_state"]["current_scenario_skill"] = skill_name if scenario else ""
        msg.update(kwargs)
        self.state["messages"].append(msg)

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
        return dict(self.state)

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
