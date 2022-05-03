import logging
import json
import os
import time
import re


from healthcheck import HealthCheck
from flask import Flask, jsonify, request

from common.gain_assistance import DEPRESSION_PATTERN, BAD_DAY_PATTERN, PROBLEMS_PATTERN
from common.get_book_recommendation import BOOKS_PATTERN, GENRES_PATTERN, RECOMMEND_BOOK_PATTERN, APPRECIATION_PATTERN, RECOMMEND_PATTERN, BOOKS_TOPIC_PATTERN
from common.tv_series_recommendation import RECOMMEND_SERIES_PATTERN
from common.get_book_information import TELL_BOOK_DESCRIPTION_PATTERN, TELL_ABOUT_BOOK_PATTERN, TELL_BOOK_AUTHOR_PATTERN, TELL_BOOK_GENRE_PATTERN
from common.test_bot import PRESIDENT_OPINION_PATTERN, SWEAR_WORDS_PATTERN
from common.travel_recommendation import TRAVEL_RECOMMENDATION_PATTERN
from common.have_fun import HAVE_FUN_PATTERN


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

share_problems_patterns = [DEPRESSION_PATTERN, BAD_DAY_PATTERN, PROBLEMS_PATTERN]
recommend_book_by_genre_patterns = [
    [BOOKS_PATTERN, APPRECIATION_PATTERN],
    [GENRES_PATTERN, APPRECIATION_PATTERN],
    [RECOMMEND_PATTERN, GENRES_PATTERN],
    BOOKS_TOPIC_PATTERN,
    RECOMMEND_BOOK_PATTERN
    ]

get_book_information_patterns = [TELL_BOOK_DESCRIPTION_PATTERN, TELL_ABOUT_BOOK_PATTERN, TELL_BOOK_AUTHOR_PATTERN, TELL_BOOK_GENRE_PATTERN]

test_bot_patterns = [PRESIDENT_OPINION_PATTERN, SWEAR_WORDS_PATTERN]


def detect_goal(requested_data):
    st_time = time.time()
    last_utterances = []
    if type(requested_data) == dict:
        for sent in requested_data['sentences']:
            last_utterances.append(sent)
    else:
        for data in requested_data:
            for sent in data['sentences']:
                last_utterances.append(sent)

    results = []
    utterances_list = []
    utterances_nums = []
    for n, utterance in enumerate(last_utterances):
         if len(utterance) > 0:
            if utterance[-1] not in {".", "!", "?"}:
                utterance = f"{utterance}."
            utterances_list.append(utterance.lower())
            utterances_nums.append(n)
    

    if utterances_list:
        for utterance in utterances_list:
            human_goal = {'human_goals': []}
            for pattern in share_problems_patterns:
                flag_problems = bool(pattern.search(utterance))
                if flag_problems:
                    human_goal["human_goals"].append('share_personal_problems')

            for pattern in recommend_book_by_genre_patterns:
                if type(pattern) == list:
                    count_patterns = 0
                    for i, pat in enumerate(pattern):
                        if re.search(pat, utterance):
                            count_patterns += 1
                    if count_patterns == len(pattern):
                        human_goal["human_goals"].append('get_book_recommendation')
                else:
                    if re.search(pattern, utterance):
                        human_goal["human_goals"].append('get_book_recommendation')

            flag_series = bool(RECOMMEND_SERIES_PATTERN.search(utterance))
            if flag_series:
                human_goal["human_goals"].append('get_series_recommendation')

            for pattern in get_book_information_patterns:
                flag_book_info = bool(pattern.search(utterance))
                if flag_book_info:
                    human_goal["human_goals"].append('get_book_information')

            for pattern in test_bot_patterns:
                flag_test_bot = bool(pattern.search(utterance))
                if flag_test_bot:
                    human_goal["human_goals"].append('test_bot')

            flag_travel_recommendation = bool(TRAVEL_RECOMMENDATION_PATTERN.search(utterance))
            if flag_travel_recommendation:
                human_goal["human_goals"].append('get_travel_recommendation')

            flag_have_fun = bool(HAVE_FUN_PATTERN.search(utterance))
            if flag_have_fun:
                human_goal["human_goals"].append('have_fun')


            results.append(list(set(human_goal["human_goals"])))

    
    total_time = time.time() - st_time
    logger.info(f"human_goals exec time: {total_time:.3f}s")
    return results


@app.route("/respond", methods=["POST"])
def respond():
    responses = detect_goal(request.json)
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)

