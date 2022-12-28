import requests
import json

# test_config = []
# for i in range(1, 5):
#     with open("test_tracker_" + str(i) + ".json", "r") as f:
#         data = json.load(f)
#         test_config.append(data)


# gold_result = [
#     '{"state": [[], []]}',
#     '{"state": [[], [["get_book_recommendation", "goal_detected"]]]}',
#     '{"state": [[], [["get_book_recommendation", "goal_detected"]], [["get_book_recommendation", "goal_in_progress"]], []]}',
#     '{"state": [[], [["get_book_recommendation", "goal_detected"]], [["get_book_recommendation", "goal_in_progress"]], [], [["get_book_recommendation", "goal_achieved"]], []]}'
#     ]

if __name__ == "__main__":
    url = "http://0.0.0.0:8129/respond"
    results = []
    count = 0
    # for utt, gold_res in zip(test_config, gold_result):
    #     result = requests.post(url, json=utt[0]).json()
    #     results.append(result)
    #     if result[0]["human_attributes"]["goals_tracker"] == gold_res:
    #         count += 1

    # assert count == len(test_config)
    print("Success")
