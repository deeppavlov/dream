# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from argparse import ArgumentParser
import pandas as pd
import json


def __main__():
    parser = ArgumentParser()
    parser.add_argument("--ratings_file", type=str, default="ratings.csv",
                        help="Ratings file")
    parser.add_argument("--dialogs_file", type=str, default="dialogs.3", help="Dialog file")
    parser.add_argument("--output_file", type=str, default="dialog_list.json", help="FIle with best dialogs")

    args = parser.parse_args()
    print('Reading ratings from file ' + str(args.ratings_file))
    ratings = pd.read_csv(args.ratings_file)
    ratings = ratings[ratings['Rating'] >= 4]
    conv_ids = ratings['Conversation ID']
    conv_ids = set(list(conv_ids))
    print('Reading dialogs from file ' + str(args.dialogs_file))
    dialogs = json.load(open(args.dialogs_file, 'r'))
    dialog_list = list()
    for dialog in dialogs:
        added = False
        utterances = dialog['utterances']
        for utterance in utterances:
            cond1 = 'attributes' in utterance and 'conversation_id' in utterance['attributes']
            if cond1 and utterance['attributes']['conversation_id'] in conv_ids and not added:
                added = True
                dialog_list.append(dialog)
    json.dump(dialog_list, open(args.output_file, 'w'))
    print('Dialogs successfully extracted into file ' + str(args.output_file))


__main__()
