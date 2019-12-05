import requests
import json
from tqdm import tqdm
import os
from argparse import ArgumentParser


def condition(scores):
    y1 = scores['isResponseOnTopic'] > 0.5
    y2 = scores['isResponseErroneous'] < 0.5
    y3 = scores['isResponseComprehensible'] > 0.5
    y4 = scores['isResponseInteresting'] > 0.5
    y5 = scores['responseEngagesUser'] > 0.5
    return y1 and y2 and y3 and y4 and y5


def process(dialog):
    return {'utterances': [utterance['text'] for utterance in dialog['utterances']]}


def to_list(dialog_file):
    dialog_list = [process(j) for j in json.load(open(dialog_file))]
    conversation_list = []
    for dialog in tqdm(dialog_list):
        utterances = dialog['utterances']
        for i in range(1, len(utterances), 2):
            currentUtterance = utterances[i - 1]
            currentResponse = utterances[i]
            if i >= 5:
                pastUtterances = [utterances[i - 5], utterances[i - 3]]
                pastResponses = [utterances[i - 4], utterances[i - 2]]
            elif i >= 3:
                pastUtterances = [utterances[i - 3]]
                pastResponses = [utterances[i - 2]]
            else:
                pastUtterances, pastResponses = [], []
            conversation_list.append({'currentUtterance': currentUtterance,
                                      'currentResponse': currentResponse,
                                      'pastUtterances': pastUtterances,
                                      'pastResponses': pastResponses})
    return conversation_list


def __main__():
    parser = ArgumentParser()
    parser.add_argument("--dialogs_file", type=str, default="dialogs.2", help="Dialog file")
    parser.add_argument("--output_file", type=str, default="cobot_dialog_list.json", help="FIle with best dialogs")
    args = parser.parse_args()
    API_KEY = os.environ.get('COBOT_API_KEY')
    SERVICE_URL = os.environ.get('COBOT_QA_SERVICE_URL')
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    conversation_list = to_list(args.dialogs_file)
    scores = []
    for i in tqdm(range(0, len(conversation_list), 100)):
        data = requests.request(url=SERVICE_URL, headers=headers,
                                data=json.dumps({'conversations': conversation_list[i:i + 100]}), method='POST').json()
        scores = scores + (data['conversationEvaluationScores'])
    conversation_list = [j for i, j in enumerate(conversation_list) if condition(scores[i])]
    dialog = [{'utterances': []}]
    for data in conversation_list:
        dialog[0]['utterances'].append(data['currentUtterance'])
        dialog[0]['utterances'].append(data['currentResponse'])
    json.dump(dialog, open(args.output_file, 'w'), indent=4)
    print('Turns are successfully written in ' + str(args.output_file))


__main__()
