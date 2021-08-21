# %%
from typing import Dict, List


from utils.candidates import sample_candidates
from utils.state import State
from utils.game_db import get_db_index

from skills.skill_scorer.skill import run_skill as skill_scorer, skill_attrs as skill_scorer_attrs
from skills.rule_based_intent.skill import run_skill as rule_based_intent, skill_attrs as rule_based_intent_attrs
from skills.tutor.skill import run_skill as tutor, skill_attrs as tutor_attrs
from skills.game_tops.skill import run_skill as game_tops, skill_attrs as game_tops_attrs
from skills.game_conversation.skill import run_skill as game_conversation, skill_attrs as game_conversation_attrs

skill_db = {}


def add_skill(func, skill_name: str = ""):
    if skill_name:
        skill_db[skill_name] = func
    else:
        skill_db[func.__name__] = func


add_skill(skill_scorer, skill_scorer_attrs.skill_name)
add_skill(rule_based_intent, rule_based_intent_attrs.skill_name)
add_skill(tutor, tutor_attrs.skill_name)
add_skill(game_tops, game_tops_attrs.skill_name)
add_skill(game_conversation, game_conversation_attrs.skill_name)

# %%


def is_last_skill(skill_name, state):
    return skill_name in state.skill_history[-1:]


def run_skills(history: List, state: Dict, agent_intents: Dict = {}):
    state = State(get_db_index(), state)
    state.add_human_message(history[-1])
    # step 0
    # get skill scores
    # state = skill_scorer(state)

    # step 1
    # try to find an intention
    state = rule_based_intent(state)
    # print(f"<main> state.intents: {state.intents}")
    # print(f"<main> state.st2_policy: {state.st2_policy}")

    # step 2
    # skill requesting policy
    scheduled_skills = []
    if len(state.utterances) <= 1:
        scheduled_skills.append((tutor_attrs.skill_name, [tutor_attrs.modes.intro]))

    elif "topic_switching" in agent_intents and not (
        ("next_game_intent" in state.intents) and is_last_skill(game_conversation_attrs.skill_name, state)
    ):
        # switch the topic
        pass
    elif (
        is_last_skill(tutor_attrs.skill_name, state)
        and ("no_intent" in state.intents or "stop_intent" in state.intents or "topic_switching" in agent_intents)
        and (
            "next_game_intent" not in state.intents
            or ("next_game_intent" in state.intents and "no_intent" in state.intents)
        )
    ):
        # switch the topic
        pass

    elif is_last_skill(tutor_attrs.skill_name, state) and (
        "yes_intent" in state.intents
        or "wanna_intent" in state.intents
        or "to_talk_about_intent" in agent_intents
        or "tell_me_more" in agent_intents
    ):
        # talk about a top
        scheduled_skills.append((game_tops_attrs.skill_name, [game_tops_attrs.modes.intro]))
    elif (
        ("stop_intent" in state.intents or "topic_switching" in agent_intents)
        and ("next_game_intent" not in state.intents)
        and ("to_talk_about_intent" not in state.intents)
    ):
        scheduled_skills.append((tutor_attrs.skill_name, [tutor_attrs.modes.stop]))
        state.interrupt_scenario()
    elif "game_tops_intent" in state.intents:
        scheduled_skills.append((game_tops_attrs.skill_name, [game_tops_attrs.modes.intro]))
    elif "to_talk_about_intent" in state.intents and state.get_content("games"):
        if is_last_skill(game_conversation_attrs.skill_name, state):
            scheduled_skills.append((game_tops_attrs.skill_name, [game_tops_attrs.modes.intro]))
        else:
            scheduled_skills.append(
                (
                    game_conversation_attrs.skill_name,
                    (
                        []
                        if is_last_skill(game_conversation_attrs.skill_name, state)
                        else [game_conversation_attrs.modes.intro]
                    ),
                )
            )
            state.interrupt_scenario()
    elif state.current_scenario_skill:
        scheduled_skills.append((state.current_scenario_skill, []))
    elif is_last_skill(game_conversation_attrs.skill_name, state) and "next_game_intent" in state.intents:
        scheduled_skills.append((game_tops_attrs.skill_name, []))
    elif "tutor_intent" in state.intents:
        scheduled_skills.append((tutor_attrs.skill_name, [tutor_attrs.modes.intro]))
    state.reset_st2_policy()
    # print(state)

    # step 3
    # skill survey
    for skill_name, modes in scheduled_skills:
        state = skill_db[skill_name](state, modes)

    # step 4
    # sampling
    hypotheses = state.hypotheses
    if hypotheses:
        response = sample_candidates([(hyp, hyp["confidence"]) for hyp in hypotheses], softmax_temperature=0.001)[-1][0]
    else:
        response = {
            "confidence": 0.0,
            "skill_name": state.skill_history[-1] if state.skill_history else "empty_answer",
            "text": "Sorry",
        }

    state.add_bot_message(**response)
    # print(state.skill_states)
    # print(state.state["content_state"])

    return response, state.to_dict()
