# from http.client import NOT_IMPLEMENTED
import re
import json
from threading import stack_size

from common.constants import GOAL_DETECTED, GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_IGNORED, GOAL_OFFERED, GOAL_REJECTED
from common.utils import yes_templates


class GoalTracker:

    map_goal2skill = None

    def __init__(self, initial_state=None):
        if initial_state:
            initial_state = self.load_dump(initial_state)
            for key, value in initial_state.items():
                setattr(self, key, value)
        else:
            self.state = []

    def update_goals_after_interlocutor(self, prev_skill_goal_status, active_skill):
        """
        updating current speaker's from the view of the interlocutor
        """
        raise NotImplementedError

    def update_goals(self, detected_goals, user_utt):
        """
        undating current speaker's goals state
        """
        raise NotImplementedError
        
    def dump_state(self):
        jsonStr = json.dumps(self.__dict__)
        return jsonStr
        
    def load_dump(self, initial_state: str):
        state_json = json.loads(initial_state)
        return state_json
        

class HumanGoalTracker(GoalTracker):

    map_goal2skill = {
            "share_personal_problems": "dff_share_problems_skill",
            "get_book_recommendation": "dff_book_recommendation_skill",
            "get_series_recommendation": "dff_series_recommendation_skill",
            "get_book_information": "dff_get_book_information_skill",
            "test_bot": "dff_test_bot_skill",
            "get_travel_recommendation": "dff_travel_recommendation_skill",
            "have_fun": "dff_have_fun_skill"
        }

    def update_goals_after_interlocutor(self, dialog):
        new_utt_goals_status = []
        prev_skill_goal_status = None
        try:
            hypotheses = dialog["human_utterances"][-2]["hypotheses"]
            active_skill = dialog["bot_utterances"][-1]["active_skill"]
            for i, hypothesis in enumerate(hypotheses): 
                if hypothesis["skill_name"] == active_skill:
                    skill_attributes = hypotheses[i]
                    break
        except:
            skill_attributes = None
            active_skill = None
        
        if skill_attributes:
            try:
                prev_skill_goal_status = skill_attributes["goal_status"]
            except:
                prev_skill_goal_status = prev_skill_goal_status
        if self.state != []:
            last_user_utt_goals = self.state[-1]
            for goal_tuple in last_user_utt_goals:
                goal = goal_tuple[0]
                status = goal_tuple[1]
                if goal in HumanGoalTracker.map_goal2skill.keys():
                    if active_skill == HumanGoalTracker.map_goal2skill[goal]:
                        if status == GOAL_DETECTED:
                            if prev_skill_goal_status == GOAL_IN_PROGRESS:
                                new_status = (goal, GOAL_IN_PROGRESS)
                            elif (prev_skill_goal_status == None) or (prev_skill_goal_status != GOAL_IN_PROGRESS):
                                new_status = (goal, GOAL_IGNORED)

                    else:
                        if status == GOAL_DETECTED:
                            new_status = (goal, GOAL_IGNORED)
                        
                    if new_status:
                        new_utt_goals_status.append(new_status)

            if self.state[-2] != []:
                last_bot_utt_goals = self.state[-2]
                for goal_tuple in last_bot_utt_goals:
                    goal = goal_tuple[0]
                    status = goal_tuple[1]
                    if goal in HumanGoalTracker.map_goal2skill.keys():
                        if active_skill == HumanGoalTracker.map_goal2skill[goal]:
                            if status == GOAL_IN_PROGRESS:
                                if (prev_skill_goal_status == GOAL_IN_PROGRESS) or (prev_skill_goal_status == GOAL_ACHIEVED) or (prev_skill_goal_status == GOAL_NOT_ACHIEVED):
                                    new_bot_status = (goal, prev_skill_goal_status)
                                elif (prev_skill_goal_status != GOAL_IN_PROGRESS) and (prev_skill_goal_status != GOAL_ACHIEVED):
                                        new_bot_status = (goal, GOAL_NOT_ACHIEVED)
                        
                        else:
                            if status == GOAL_IN_PROGRESS:
                                new_bot_status = (goal, GOAL_NOT_ACHIEVED)

                        try:
                            new_utt_goals_status.append(new_bot_status)
                        except:
                            pass


        if prev_skill_goal_status == GOAL_OFFERED:
            for goal, skill in HumanGoalTracker.map_goal2skill.items():
                if skill == active_skill:
                    new_utt_goals_status.append((goal, GOAL_OFFERED))
            
        self.state.append(new_utt_goals_status)

    def update_goals(self, dialog):
        curr_hum_utt_status = []
        user_utt = dialog["utterances"][-1]["text"]
        detected_goals = dialog["human_utterances"][-1].get("annotations", {}).get("human_goals_detector", [])
        list_prev_goals = []
        if self.state[-1]:
            for goal_prev, status in self.state[-1]:
                 list_prev_goals.append(goal_prev)

        if detected_goals:
            for goal in detected_goals:
                if goal not in list_prev_goals:
                    curr_hum_utt_status.append((goal, GOAL_DETECTED))
        
        if self.state[-1]:
            for goal, status in self.state[-1]:
                if status == GOAL_OFFERED:
                    if bool(yes_templates.search(user_utt)):
                        curr_hum_utt_status.append((goal, GOAL_DETECTED))
                    else:
                        curr_hum_utt_status.append((goal, GOAL_REJECTED))

        self.state.append(curr_hum_utt_status)
