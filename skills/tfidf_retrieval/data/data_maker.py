# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from argparse import ArgumentParser
import pandas as pd
import json
import os
from tqdm import tqdm
from deeppavlov import configs, build_model


def process(dialog, gold_list, ner_model):
    utterances = [utterance['text'] for utterance in dialog['utterances']]
    for i in range(len(utterances)):
        if utterances[i] in gold_list:
            utterances[i + 1] = 'NO_ANSWER'
        elif i % 2 != 0 and 'PER' in ''.join(ner_model([utterances[i]])[1][0]):
            utterances[i] = 'NO_ANSWER'
    return {'conversation_id': dialog['utterances'][0]['attributes']['conversation_id'],
            'utterances': [utterance['text'] for utterance in dialog['utterances']]}


def increment(filename):
    prefix, num = filename.split('_v')
    num = num.split('.json')[0]
    try:
        num = int(num)
    except BaseException:
        raise Exception('Version num ' + num + ' is not convertible to int')
    num += 1
    return prefix + '_v' + str(num) + '.json'


def condition(utterance, used_ids):
    '''
    This function was added to bypass fucking PEP8
    '''
    try:
        return utterance['attributes']['conversation_id'] not in used_ids
    except BaseException:
        return False


def __main__():
    parser = ArgumentParser()
    parser.add_argument("--ratings_file", type=str, default="ratings/ratings.csv",
                        help="Ratings file")
    parser.add_argument("--dialogs_file", type=str, default="dialogs", help="Dialog file")
    parser.add_argument("--output_file", type=str, default="skills/tfidf_retrieval/data/dialog_list_v1.json",
                        help="File with the best dialogs")
    parser.add_argument("--bad_output_file", type=str, default="skills/tfidf_retrieval/data/bad_dialog_list_v1.json",
                        help="File with the worst dialogs")
    parser.add_argument("--assessment_file", type=str, default=None,
                        help='All available conversation assessment files merged into one')
    parser.add_argument("--good_poor_phrase_file", type=str, default='skills/tfidf_retrieval/data/goodpoor.json',
                        help='Output with good and poor pairs')
    parser.add_argument("--gold_phrase_file", type=str, default='tests/dream/test_dialogs_gold_phrases.csv',
                        help='Output with good and poor pairs')
    ner_model = build_model(configs.ner.ner_conll2003_bert, download=True)
    args = parser.parse_args()
    old_output_file = args.output_file
    while os.path.exists(increment(old_output_file)):
        old_output_file = increment(old_output_file)
    try:
        good_dialogs = json.load(open(old_output_file, 'r'))
        output_file = increment(old_output_file)
    except BaseException:
        print('No previous output file found')
        good_dialogs = []
        output_file = old_output_file
    if args.bad_output_file:
        old_bad_output_file = args.bad_output_file
        while os.path.exists(increment(old_bad_output_file)):
            old_bad_output_file = increment(old_bad_output_file)
        try:
            bad_dialogs = json.load(open(old_bad_output_file, 'r'))
            bad_output_file = increment(old_bad_output_file)
        except BaseException:
            print('No previous bad output file found')
            bad_dialogs = []
            bad_output_file = old_bad_output_file
    else:
        bad_dialogs = []
    used_ids = set([dialog['conversation_id'] for dialog in good_dialogs + bad_dialogs])
    assert '_v' in args.output_file, 'Requires version in output'
    if args.bad_output_file:
        assert '_v' in args.bad_output_file, 'Requires version in bad output'
    gold_phrases = open(args.gold_phrase_file, 'r').readlines()[1:]
    gold_list = []
    for gold_phrase in gold_phrases:
        if gold_phrase[0] == '"':
            gold_phrase = gold_phrase[1:]
        gold_phrase = gold_phrase.split('"\n')[0].split('" "')[0].lower()
        gold_list.append(gold_phrase)
    print('Reading ratings from file ' + str(args.ratings_file))
    ratings = pd.read_csv(args.ratings_file)
    good_ratings = ratings[ratings['Rating'] >= 5]
    good_ids = set(list(good_ratings['Conversation ID']))
    if args.bad_output_file:
        bad_ratings = ratings[ratings['Rating'] <= 2]
        bad_ids = set(list(bad_ratings['Conversation ID']))
    print('Reading dialogs from file ' + str(args.dialogs_file))
    dialogs = json.load(open(args.dialogs_file, 'r'))
    poor_turns = set()
    good_turns = set()
    good_poor_phrases = [{'good': {}, 'poor': {}}]
    if args.assessment_file is not None:
        assessment = pd.read_csv(args.assessment_file)
        assessment_ids = set(assessment['conversation_id'])
        for i in assessment.index:
            if assessment['alexaResponseQuality'][i] in ['notGood', 'poor']:
                poor_turns.add((assessment['conversation_id'][i],
                                assessment['turn_number'][i]))
            if assessment['alexaResponseQuality'][i] in ['good', 'excellent']:
                good_turns.add((assessment['conversation_id'][i],
                                assessment['turn_number'][i]))
        dialog_list = []
        for j in dialogs:
            cond1 = 'conversation_id' in j['utterances'][0]['attributes']
            if cond1:
                conv_id = j['utterances'][0]['attributes']['conversation_id']
                if conv_id in assessment_ids and conv_id not in used_ids:
                    dialog_list.append(j)
        for dialog in dialog_list:
            id_ = dialog['utterances'][0]['attributes']['conversation_id']
            len_ = len(dialog['utterances'])
            for i in range(1, len_, 2):
                bot_phrase = dialog['utterances'][i]['text']
                user_phrase = dialog['utterances'][i - 1]['text']
                utterance_num = i // 2
                if (id_, utterance_num) in good_turns and '#+#' not in bot_phrase:
                    good_poor_phrases[0]['good'][user_phrase] = bot_phrase
                if (id_, utterance_num) in poor_turns:
                    good_poor_phrases[0]['poor'][user_phrase] = bot_phrase
        json.dump(good_poor_phrases, open(args.good_poor_phrase_file, 'w'), indent=4)

    for dialog in tqdm(dialogs):
        added = False
        utterances = [utterance for utterance in dialog['utterances'] if condition(utterance, used_ids)]
        for utterance in utterances:
            cond1 = utterance['attributes']['conversation_id'] in good_ids
            cond2 = len(dialog['utterances']) >= 7
            if cond1 and cond2 and not added:
                added = True
                good_dialogs.append(process(dialog, gold_list, ner_model))
            if args.bad_output_file:
                if utterance['attributes']['conversation_id'] in bad_ids and not added:
                    added = True
                    bad_dialogs.append(process(dialog, gold_list, ner_model))
    json.dump(good_dialogs, open(output_file, 'w'), indent=4)
    print('Dialogs successfully extracted into file ' + str(args.output_file))
    if args.bad_output_file:
        json.dump(bad_dialogs, open(bad_output_file, 'w'), indent=4)
    print('Bad dialogs successfully extracted into file ' + str(args.bad_output_file))


__main__()
