import requests

test_config = [
        {
            "last_detected_goals": [],
            "goals_tracker_state": [],
            "skill_goal_status": None,
            "last_active_skill": None
        },
        {
            "last_detected_goals": ["share_personal_problems"],
            "goals_tracker_state": [[], []],
            "skill_goal_status": None,
            "last_active_skill": "dff_template_skill"
        },
        {
            "last_detected_goals": ["get_book_recommendation"],
            "goals_tracker_state": [[], [], [], [("share_personal_problems", "goal_detected")]],
            "skill_goal_status": "goal_in_progress",
            "last_active_skill": "dff_share_problems_skill"
        },
        {
            "last_detected_goals": [],
            "goals_tracker_state": [[], [], [], [("share_personal_problems", "goal_detected")], [("share_personal_problems", "goal_in_progress")],
     [("share_personal_problems", "goal_in_progress"), ("get_book_recommendation", "goal_detected")],
     [("share_personal_problems", "goal_in_progress"), ("get_book_recommendation", "goal_ignored")],
     [("share_personal_problems", "goal_in_progress")]],
            "skill_goal_status": "goal_achieved",
            "last_active_skill": "dff_share_problems_skill"
        },
    ]

gold_result = [
    [[], []],
    [[], [], [], [("share_personal_problems", "goal_detected")]],
    [[], [], [], [("share_personal_problems", "goal_detected")], [("share_personal_problems", "goal_in_progress")],
    [("get_book_recommendation", "goal_detected"), ("share_personal_problems", "goal_in_progress")]],
    [[], [], [], [("share_personal_problems", "goal_detected")], [("share_personal_problems", "goal_in_progress")],
     [("share_personal_problems", "goal_in_progress"), ("get_book_recommendation", "goal_detected")],
     [("share_personal_problems", "goal_in_progress"), ("get_book_recommendation", "goal_ignored")],
     [("share_personal_problems", "goal_in_progress")],
     [("share_personal_problems", "goal_achieved")],
     []]
]

if __name__ == "__main__":
    url = "http://0.0.0.0:8125/respond"
    results = []
    count = 0
    for utt, gold_res in zip(test_config, gold_result):
        # result = requests.post(url, json=utt).json()
        result = requests.post(url, json=utt)
        print(result)
        results.append(result)
        if result == gold_res:
            count += 1
        
    assert count != len(test_config)
    print("Success")
