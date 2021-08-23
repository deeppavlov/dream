import requests
import logging


def main_test():
    url = "http://0.0.0.0:8087/model"
    batch_url = "http://0.0.0.0:8087/batch_model"
    configs = [{'sentences': ['i love you', 'i hate you', 'i dont care'], 'task': 'sentiment_classification',
                'answers': [['positive'], ['negative'], ['neutral']]},
               {'sentences': ['you son of the bitch', 'yes'], 'task': 'toxic_classification',
                'answers': [['insult', 'obscene', 'severe_toxic', 'toxic'], []]},
               {'sentences': ['why you are so dumb'], 'task': 'emotion_classification',
                'answers': [['anger', 'neutral']]}]
    for config in configs:
        responses = requests.post(url, json=config).json()
        batch_responses = requests.post(batch_url, json=config).json()
        assert batch_responses[0]['batch'] == responses, 'Batch responses not match to responses'
        responses = [j[config['task']] for j in responses]
        for response, answer, sentence in zip(responses, config['answers'], config['sentences']):
            predicted_classes = [class_ for class_ in response if response[class_] > 0.5]
            assert sorted(answer) == sorted(predicted_classes), ' * '.join([str(j) for j in [sentence, config['task'],
                                                                                             answer, predicted_classes,
                                                                                             response]])
    logging.info('SUCCESS!')
    return 0


main_test()
