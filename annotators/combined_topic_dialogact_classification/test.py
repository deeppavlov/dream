import requests
import logging


def main_test():
    url = "http://0.0.0.0:8118/model"
    batch_url = "http://0.0.0.0:8118/batch_model"
    configs = [{'phrase': ['your favourite football team', 'have you ever heard about rap music'],
                'history': ['yes', 'and [SEP] you', ],
                'task': 'cobot_topics',
                'answers': [['Sports'], ['Music']]},
               {'phrase': ['What is your favourite book?', 'Have you watched Avatar?'],
                'history': ['yes', 'a [SEP] OK'],
                'task': 'cobot_dialogact_topics',
                'answers': [['Entertainment_Books'], ['Entertainment_Movies']]},
               {'phrase': ['who is john biden', 'i want to switch topic'],
                'history': ['yes', 'a [SEP] OK'],
                'task': 'cobot_dialogact_intents',
                'answers': [['Information_RequestIntent'], ['Topic_SwitchIntent']]}]
    for config in configs:
        responses = requests.post(url, json=config).json()
        batch_responses = requests.post(batch_url, json=config).json()
        assert batch_responses[0]['batch'] == responses, 'Batch responses not match to responses'
        responses = [j[config['task']] for j in responses]
        for response, answer, phrase, history in zip(responses, config['answers'], config['phrase'], config['history']):
            predicted_classes = [class_ for class_ in response if response[class_] > 0.5]
            assert sorted(answer) == sorted(predicted_classes), ' * '.join([str(j) for j in [phrase, history,
                                                                                             config['task'],
                                                                                             answer, predicted_classes,
                                                                                             response]])
    logging.info('SUCCESS!')
    return 0


main_test()
