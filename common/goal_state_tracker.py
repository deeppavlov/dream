# from http.client import NOT_IMPLEMENTED
from common.constants import GOAL_DETECTED, GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_IGNORED, GOAL_OFFERED, GOAL_REJECTED

class GoalTracker:

    map_goal2skill = {
            "share_personal_problems": "dff_share_problems_skill",
            "get_book_recommendation": "dff_book_recommendation_skill"
        }

    def __init__(self):
        self.state = []
        
        
    def load_state(self, prev_goals_state):
        if prev_goals_state:
            self.state = prev_goals_state

    
    def update_human_goals_from_bot(self, prev_skill_goal_status, active_skill):
        new_utt_goals_status = []
        if self.state != []:
            last_user_utt_goals = self.state[-1]
            for goal_tuple in last_user_utt_goals:
                goal = goal_tuple[0]
                status = goal_tuple[1]
                if goal in GoalTracker.map_goal2skill.keys():
                    if active_skill == GoalTracker.map_goal2skill[goal]:
                        if status == GOAL_DETECTED:
                            if prev_skill_goal_status == GOAL_IN_PROGRESS:
                                new_status = (goal, GOAL_IN_PROGRESS)
                            elif (prev_skill_goal_status == None) or (prev_skill_goal_status != GOAL_IN_PROGRESS):
                                new_status = (goal, GOAL_IGNORED)
                    
                        elif status == GOAL_IN_PROGRESS:
                            if (prev_skill_goal_status == GOAL_IN_PROGRESS) or (prev_skill_goal_status == GOAL_ACHIEVED):
                                new_status = (goal, prev_skill_goal_status)
                            elif (prev_skill_goal_status != GOAL_IN_PROGRESS) and (prev_skill_goal_status != GOAL_ACHIEVED):
                                    new_status = (goal, GOAL_NOT_ACHIEVED)

                    else:
                        if status == GOAL_DETECTED:
                            new_status = (goal, GOAL_IGNORED)
                        elif status == GOAL_IN_PROGRESS:
                            new_status = (goal, GOAL_NOT_ACHIEVED)
                        
                    if new_status:
                        new_utt_goals_status.append(new_status)
            
        if prev_skill_goal_status == GOAL_OFFERED:
            for goal, skill in GoalTracker.map_goal2skill.items():
                print(skill)
                print(active_skill)
                if skill == active_skill:
                    new_utt_goals_status.append((goal, GOAL_OFFERED))
            
        self.state.append(new_utt_goals_status)


    def update_human_goals(self, detected_goals, active_skill):
        curr_hum_utt_status = []
        if detected_goals:
            for goal in detected_goals:
                curr_hum_utt_status.append((goal, GOAL_DETECTED))
        
        if self.state[-1]:
            for goal, status in self.state[-1]:
                if status == GOAL_IN_PROGRESS:
                    curr_hum_utt_status.append((goal, status))
                elif status == GOAL_OFFERED:
                    print(active_skill)
                    print(GoalTracker.map_goal2skill[goal])
                    if active_skill == GoalTracker.map_goal2skill[goal]:
                        curr_hum_utt_status.append((goal, GOAL_DETECTED))
                    else:
                        curr_hum_utt_status.append((goal, GOAL_REJECTED))

        self.state.append(curr_hum_utt_status)
    

    def save_state(self):
        return self.state
        

        
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
# [('get_recommendation_book', GOAL_ACHIEVED)], user
#  [('get_recommendation_movie', GOAL_OFFERED)], bot
# [('get_recommendation_movie', GOAL_DETECTED)], user
# [('get_recommendation_movie', GOAL_IN_PROGRESS)], bot
# [('get_recommendation_movie', GOAL_NOT_ACHIEVED)]]  user


# трекер вызывается после детектора (в аннотаторах), и загружает, обновляет стейт и потом сохраняет в хьюман атрибуты
# 

# есть респонс от скилла - tuple с несколькими эл-ами: 
# ('hello', 0.9, {'human_goals_status': ('get_recommendation_book', GOAL_IN_PROGRESS)}, {}, {})

# как получить атрибуты реплики: они есть только в гипотезах - у меня есть bot_utterances и айдишники, и я могу найти словарь, который
#  соответсвует этому 

# dialog["human_utterances"][-1]["hypotheses"][i]["attributes"] # i corresponds to final hypotheses

# тут ищу ключ


