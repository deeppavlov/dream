import logging
import json
import os
import time
import re


# import sentry_sdk
from healthcheck import HealthCheck
from flask import Flask, jsonify, request

from common.gain_assistance import DEPRESSION_PATTERN, BAD_DAY_PATTERN, PROBLEMS_PATTERN
from common.get_book_recommendation import BOOKS_PATTERN, GENRES_PATTERN, RECOMMEND_BOOK_PATTERN
from common.get_book_info import BOOK_INFO_PATTERN

# sentry_sdk.init(os.getenv("SENTRY_DSN")) эта штука всегда и везде не работает, потому что SENTRY_DSN не прописан

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

share_problems_patterns = [DEPRESSION_PATTERN, BAD_DAY_PATTERN, PROBLEMS_PATTERN]
recommend_book_by_genre_patterns = [BOOKS_PATTERN, GENRES_PATTERN, RECOMMEND_BOOK_PATTERN]


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
                flag_rec_book = bool(pattern.search(utterance))
                if flag_rec_book:
                    human_goal["human_goals"].append('get_book_recommendation')

            flag_book_info = bool(BOOK_INFO_PATTERN.search(utterance))
            if flag_book_info:
                human_goal["human_goals"].append('get_information_about_book')


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

