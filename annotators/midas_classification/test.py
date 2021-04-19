import requests
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

test_config = {'dialogs': [{'human_utterances': [{'text': 'this is the best dog'}],
                            'bot_utterances': [{'text': 'so what you think ha'}]}],
               'threshold': 0}
test_config_reverted = {'sentences': ['this is the best dog'],
                        'last_human_utterances': ['so what you think ha'],
                        'threshold': 0}
gold_result = {
    'opinion': 0.6699745, 'pos_answer': 0.00049586035, 'statement': 0.20634566,
    'neg_answer': 0.001343765, 'yes_no_question': 0.006176666, 'other_answers': 0.003905255,
    'open_question_factual': 0.034658864, 'open_question_opinion': 0.07709945
}


def main_test():
    url = "http://0.0.0.0:8090/model"
    batch_url = "http://0.0.0.0:8090/batch_model"
    responses = requests.post(url, json=test_config).json()
    batch_responses = requests.post(batch_url, json=test_config_reverted).json()
    assert batch_responses[0]['batch'] == responses, f'Batch responses {batch_responses} not match' \
                                                     f'to responses {responses}'

    assert round(responses[0]["opinion"], 5) == 0.66997, print(responses)

    logger.info('Success')


if __name__ == '__main__':
    main_test()
