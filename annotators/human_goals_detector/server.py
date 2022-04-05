import logging
import json
import os
import time

# import sentry_sdk
from healthcheck import HealthCheck
from flask import Flask, jsonify, request


# sentry_sdk.init(os.getenv("SENTRY_DSN")) эта штука всегда и везде не работает, потому что SENTRY_DSN не прописан

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

gain_assistance_checklist = ['problem with', 'problems with', 'trouble with', 'trouble with',
'difficulty', 'feel bad', 'feel awful', 'suicide', 'death', 'kill myself', 'tired', "bad day",
"awful day", "hard day", "feel sad"]
recommend_book_by_genre_checklist = ['fantasy', 'historical', 'dystopian', 'recommend a book', 'harry potter', 'war and peace',
 '1984', 'recommend a book', 'what book would you suggest', 'recommend a dystopian novel',
 'recommend a historical novel', 'recommend a fantasy novel']
get_info_book_checklist = ['tell me about harry potter', 'tell me about war and peace', 'tell me about little prince']


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
            for gain_assist in gain_assistance_checklist:
                if gain_assist in utterance:
                    human_goal["human_goals"].append('gain_assistance')
            for rec_book in recommend_book_by_genre_checklist:
                if rec_book in utterance:
                    human_goal["human_goals"].append('recommend_book_by_genre')
            for get_info in get_info_book_checklist:
                if get_info in utterance:
                    human_goal["human_goals"].append('get_information_about_book')

            results.append([human_goal])

    total_time = time.time() - st_time
    logger.info(f"human_goals exec time: {total_time:.3f}s")
    return results


@app.route("/respond", methods=["POST"])
def respond():
    responses = detect_goal(request.json)
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)

