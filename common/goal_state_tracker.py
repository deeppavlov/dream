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
            "get_book_recommendation": "dff_book_recommendation_skill"
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
                    
                        # elif status == GOAL_IN_PROGRESS:
                        #     if (prev_skill_goal_status == GOAL_IN_PROGRESS) or (prev_skill_goal_status == GOAL_ACHIEVED):
                        #         new_status = (goal, prev_skill_goal_status)
                        #     elif (prev_skill_goal_status != GOAL_IN_PROGRESS) and (prev_skill_goal_status != GOAL_ACHIEVED):
                        #             new_status = (goal, GOAL_NOT_ACHIEVED)

                    else:
                        if status == GOAL_DETECTED:
                            new_status = (goal, GOAL_IGNORED)
                        # elif status == GOAL_IN_PROGRESS:
                        #     new_status = (goal, GOAL_NOT_ACHIEVED)
                        
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
                                if (prev_skill_goal_status == GOAL_IN_PROGRESS) or (prev_skill_goal_status == GOAL_ACHIEVED):
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
                # if self.state[-1]:
                #     for goal_prev, status in self.state[-1]:

                #         if goal == goal_prev:
                #             if (status == GOAL_IN_PROGRESS) or (status == GOAL_DETECTED):
                #                 statuses.append(GOAL_IN_PROGRESS)
                        
                #         else:
                #             statuses.append(GOAL_DETECTED)
                
                # if GOAL_IN_PROGRESS in statuses:
                #     curr_hum_utt_status.append((goal, GOAL_IN_PROGRESS))
                # else:
                #     curr_hum_utt_status.append((goal, GOAL_DETECTED))
                        
                #     for goal_prev, status in self.state[-1]:
                        

                #             else:
                #                 curr_hum_utt_status.append((goal, GOAL_DETECTED))


                #         if goal != goal_prev:
                #             curr_hum_utt_status.append((goal, GOAL_DETECTED))
                #         else:
                #             if (status == GOAL_IN_PROGRESS) or (status == GOAL_DETECTED):
                #                  curr_hum_utt_status.append((goal, GOAL_IN_PROGRESS))

                # else:
                #     curr_hum_utt_status.append((goal, GOAL_DETECTED))
        
        if self.state[-1]:
            for goal, status in self.state[-1]:
                # if status == GOAL_IN_PROGRESS:
                #     curr_hum_utt_status.append((goal, status))
                if status == GOAL_OFFERED:
                    if bool(yes_templates.search(user_utt)):
                        curr_hum_utt_status.append((goal, GOAL_DETECTED))
                    else:
                        curr_hum_utt_status.append((goal, GOAL_REJECTED))

        self.state.append(curr_hum_utt_status)
        



        
# обсудить с Дилей, что трекер может лежать в постаннотаторах, чтобы оценивать текущую реплику юзера и следующую реплику бота,
# которую мы собираемся выдать пользователю 


                



#  правила для обновления стейта трекера:
# 1) если предыдущий статус (статус юзера) == GOAL_DETECTED, а статус скилла == GOAL_IN_PROGRESS,
# то все ок и мы записываем новый статус (goal, GOAL_IN_PROGRESS)
# 2) если предыдущий статус юзера == GOAL_DETECTED, а статус скилла != GOAL_IN_PROGRESS,
# то новый статус = (goal, GOAL_IGNORED)
# 3) если предыдущий статус юзера == GOAL_IN_PROGRESS, а статус скилла == GOAL_IN_PROGRESS/GOAL_ACHIEVED,
# то записываем новый статус (goal, GOAL_IN_PROGRESS/GOAL_ACHIEVED)
# 4) если предыдущий статус юзера == GOAL_IN_PROGRESS, а статус скилла != GOAL_IN_PROGRESS/GOAL_ACHIEVED,
# то записываем (goal, GOAL_NOT_ACHIEVED)
# везде еще надо проверять, что какой-либо флаг вообще есть


























    # def update_human_goals(self, goal_detector_state):
        


    # def update_state(self):
    #     raise NotImplementedError


    # def dump_state(self):


    # def load_state(self):
        #  опять ВОПРОС: как вот это должно работать?
    

# 
# goals_seq = [[('get_recommendation_book', GOAL_DETECTED), ('get_recommendation_movie', GOAL_DETECTED)], user
#  [('get_recommendation_book', GOAL_IN_PROGRESS), ('get_recommendation_movie', GOAL_IGNORED)], bot
# [], user
#  [('get_recommendation_book', GOAL_ACHIEVED)], bot
# [('get_recommendation_movie', GOAL_DETECTED)], user
# [('get_recommendation_movie', GOAL_IN_PROGRESS)], bot
# [], USER
# [('get_recommendation_movie', GOAL_NOT_ACHIEVED)]]  bot


# трекер вызывается после детектора (в аннотаторах), и загружает, обновляет стейт и потом сохраняет в хьюман атрибуты
# 

# есть респонс от скилла - tuple с несколькими эл-ами: 
# ('hello', 0.9, {'human_goals_status': ('get_recommendation_book', GOAL_IN_PROGRESS)}, {}, {})

# как получить атрибуты реплики: они есть только в гипотезах - у меня есть bot_utterances и айдишники, и я могу найти словарь, который
#  соответсвует этому 

# dialog["human_utterances"][-1]["hypotheses"][i]["attributes"] # i corresponds to final hypotheses

# тут ищу ключ


