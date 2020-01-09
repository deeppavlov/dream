# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import json
from argparse import ArgumentParser


def __main__():
    parser = ArgumentParser()
    parser.add_argument("--dialogs_dir", type=str, default="dialog_data",
                        help="Ratings file")
    parser.add_argument("--output_file", type=str, default="dialogs", help="File with the best dialogs")
    args = parser.parse_args()
    final_jsons = [json.load(open(args.dialogs_dir + '/' + file_, 'r')) for file_ in os.listdir(args.dialogs_dir)]
    final_data = []
    id_set = set()
    for dialog_list in final_jsons:
        for dialog in dialog_list:
            if dialog['id'] not in id_set:
                id_set.add(dialog['id'])
                final_data.append(dialog)
    json.dump(final_data, open(args.output_file, 'w'), indent=4)


__main__()
