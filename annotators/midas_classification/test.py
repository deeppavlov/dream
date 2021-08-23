import requests
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

test_config = {'dialogs': [{'human_utterances': [{'text': 'this is the best dog'}],
                            'bot_utterances': [{'text': 'so what you think ha'}]}]}
test_config_reverted = {'sentences': ['this is the best dog'],
                        'last_human_utterances': ['so what you think ha']}
gold_result = {
    'appreciation': 0.0716494619846344, 'command': 0.0030570626258850098, 'comment': 0.7691837549209595,
    'complaint': 0.02454354055225849, 'dev_command': 0.006282569374889135, 'neg_answer': 0.0028412530664354563,
    'open_question_factual': 0.004046098794788122, 'open_question_opinion': 0.002423756755888462,
    'opinion': 0.048794493079185486, 'other_answers': 0.005758579820394516, 'pos_answer': 0.004446228966116905,
    'statement': 0.05326918140053749, 'yes_no_question': 0.003704074304550886
}


def main_test():
    url = "http://0.0.0.0:8090/model"
    batch_url = "http://0.0.0.0:8090/batch_model"
    responses = requests.post(url, json=test_config).json()
    batch_responses = requests.post(batch_url, json=test_config_reverted).json()
    assert batch_responses[0]['batch'] == responses, f'Batch responses {batch_responses} not match' \
                                                     f'to responses {responses}'

    assert round(responses[0][0]["comment"], 5) == 0.76918, print(responses)

    logger.info('Success')


if __name__ == '__main__':
    main_test()
