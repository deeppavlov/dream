# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from argparse import ArgumentParser
import pandas as pd
import json


def process(dialog):
    return {'utterances': [utterance['text'] for utterance in dialog['utterances']]}


def __main__():
    parser = ArgumentParser()
    parser.add_argument("--ratings_file", type=str, default="ratings.csv",
                        help="Ratings file")
    parser.add_argument("--dialogs_file", type=str, default="dialogs", help="Dialog file")
    parser.add_argument("--output_file", type=str, default="dialog_list.json", help="File with the best dialogs")
    parser.add_argument("--bad_output_file", type=str, default="bad_dialog_list.json",
                        help="File with the worst dialogs")
    parser.add_argument("--assessment_file", type=str, default='conversation_assessment.csv',
                        help='All available conversation assessment files merged into one')
    parser.add_argument("--good_poor_phrase_file", type=str, default='goodpoor.json',
                        help='Output with good and poor pairs')
    args = parser.parse_args()

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
        dialog_list = [j for j in dialogs if 'conversation_id' in j['utterances'][0]['attributes'] and (
                       j['utterances'][0]['attributes']['conversation_id'] in assessment_ids)]
        for dialog in dialog_list:
            id_ = dialog['utterances'][0]['attributes']['conversation_id']
            for i in range(1, len(dialog['utterances']), 2):
                bot_phrase = dialog['utterances'][i]['text']
                user_phrase = dialog['utterances'][i - 1]['text']
                utterance_num = i // 2
                if (id_, utterance_num) in good_turns and '#+#' not in bot_phrase:
                    good_poor_phrases[0]['good'][user_phrase] = bot_phrase
                if (id_, utterance_num) in poor_turns:
                    good_poor_phrases[0]['poor'][user_phrase] = bot_phrase
        json.dump(good_poor_phrases, open(args.good_poor_phrase_file, 'w'), indent=4)
    good_dialogs = []
    bad_dialogs = []
    for dialog in dialogs:
        added = False
        utterances = dialog['utterances']
        for utterance in utterances:
            cond1 = 'attributes' in utterance and 'conversation_id' in utterance['attributes']
            if cond1 and utterance['attributes']['conversation_id'] in good_ids and not added:
                added = True
                good_dialogs.append(process(dialog))
            if args.bad_output_file and cond1:
                if utterance['attributes']['conversation_id'] in bad_ids and not added:
                    added = True
                    bad_dialogs.append(process(dialog))
    json.dump(good_dialogs, open(args.output_file, 'w'), indent=4)
    print('Dialogs successfully extracted into file ' + str(args.output_file))
    if args.bad_output_file:
        json.dump(bad_dialogs, open(args.bad_output_file, 'w'), indent=4)
        print('Bad dialogs successfully extracted into file ' + str(args.bad_output_file))


__main__()
