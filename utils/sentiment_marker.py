# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 15:21:52 2020

@author: dimakarp1996
"""
import os
from argparse import ArgumentParser
from tqdm import tqdm
from requests import post, get
import json


def __main__():
    parser = ArgumentParser()
    parser.add_argument("--dialogs", type=str, default="amazon_dialogs_all.txt",
                        help="Dialog file")
    parser.add_argument("--request_url", type=str, default='http://10.11.1.5:8024/model',
                        help='url with sentiment model')
    parser.add_argument('--save_with_sentiment', action='store_true', default=False,
                        help='save dialogs file with sentiment labels')
    parser.add_argument("--output", type=str, default="amazon_dialogs_all_with_sentiment.txt",
                        help="File with sentiment labels")
    parser.add_argument("--cached_sentiment_url", type=str,
                        default="http://lnsigo.mipt.ru/export/alexaprize_data/cached_sentiment.json",
                        help="URL of cached sentiment")
    parser.add_argument("--cached_sentiment_dir", type=str,
                        default="cached_sentiment.json",
                        help="Directory of cached sentiment to save")
    args = parser.parse_args()
    if os.path.exists(args.cached_sentiment_dir):
        sentiment_dict = json.load(open(args.cached_sentiment_dir, 'r'))
    else:
        try:
            sentiment_dict = json.loads(get(args.cached_sentiment_url).text)
        except BaseException:
            sentiment_dict = dict()
    dialogs = open(args.dialogs, 'r').readlines()
    abbrev = {'negative': '-', 'neutral': '=', 'positive': '+'}
    for i in tqdm(range(len(dialogs))):
        line = dialogs[i]
        if 'Human:' == line[:6]:
            phrase = line[6:].strip()
            if phrase not in sentiment_dict:
                result = post(args.request_url, json={"sentences": [phrase]}).json()
                sentiment = abbrev[result[0][0][0]]
                sentiment_dict[phrase] = sentiment
            else:
                sentiment = sentiment_dict[phrase]
            dialogs[i] = 'Human(' + sentiment + '): ' + phrase + '\n'
    if args.save_with_sentiment:
        output_file = open(args.output, 'w')
        for line in dialogs:
            output_file.write(line)
        output_file.close()
    json.dump(sentiment_dict, open(args.cached_sentiment_dir, 'w'), indent=1)
    print('Done')


__main__()
