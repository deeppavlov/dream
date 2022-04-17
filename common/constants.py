CAN_NOT_CONTINUE = "no"
CAN_CONTINUE_SCENARIO = "can"
MUST_CONTINUE = "must"
CAN_CONTINUE_PROMPT = "can_prompt"

GOAL_DETECTED = 'goal_detected'
GOAL_IN_PROGRESS = 'goal_in_progress'
GOAL_ACHIEVED = 'goal_achieved'
GOAL_NOT_ACHIEVED = 'goal_not_achieved' # начали выполнять, но не выполнили
GOAL_IGNORED = 'goal_ignored' # вообще не начали выполнять
GOAL_OFFERED = 'goal_offered'
GOAL_REJECTED = 'goal_rejected' # только для случаев, когда мы предложили цель, а юзер отказался