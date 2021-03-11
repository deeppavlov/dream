import requests
import logging

test_config = {'dialogs': [{'human_utterances': [{'text': 'i love you'}],
                            'bot_utterances': [{'text': 'i hate you'}]}]}
test_config_reverted = {'sentences': ['i love you'],
                        'last_human_utterances': ['i hate you']}
test_config_order = ['open_question_opinion', 'open_question_personal',
                     'clarifying_question', 'correction', 'opening',
                     'uncertain', 'open_question_factual', 'non_compliant',
                     'neg_answer', 'command', 'dev_command', 'yes_no_question',
                     'appreciation', 'closing', 'other_answers', 'nonsense',
                     'pos_answer', 'complaint', 'comment', 'hold',
                     'back-channeling', 'abandon', 'opinion', 'statement']


def main_test():
    url = "http://0.0.0.0:8090/model"
    batch_url = "http://0.0.0.0:8090/batch_model"
    responses = requests.post(url, json=test_config).json()
    batch_responses = requests.post(batch_url, json=test_config_reverted).json()
    assert batch_responses[0]['batch'] == responses, f'Batch responses {batch_responses} not match' \
                                                     f'to responses {responses}'
    predicted_order = sorted(responses[0], key=responses[0].get)
    assert predicted_order == test_config_order, predicted_order
    logging.info('MIDAS test passed')


main_test()
