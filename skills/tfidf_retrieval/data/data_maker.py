from argparse import ArgumentParser
import pandas as pd
import json
import os
from tqdm import tqdm
from deeppavlov import configs, build_model
import datetime


def process(dialog, gold_list, banned_words, ner_model):
    utterances = [utterance['text'] for utterance in dialog['utterances']]
    for i in range(len(utterances) - 1):
        if utterances[i] in gold_list:
            utterances[i + 1] = ''
        utterances[i] = utterances[i].replace(',', ' ')
        cond1 = ner_model is None or 'PER' in ''.join(ner_model([utterances[i]])[1][0]) or 'Dilyara' in utterances[i]
        cond2 = ([banned_word in utterances[i] for banned_word in banned_words])
        if i % 2 != 0 and (cond1 or cond2):
            utterances[i] = ''
    return {'id': dialog['utterances'][0]['attributes']['conversation_id'],
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


def filter_gold(good_dialogs, gold_phrases, banned_words):
    for i in range(len(good_dialogs)):
        len1 = len(good_dialogs[i]['utterances'])
        for j in range(len1):
            if good_dialogs[i]['utterances'][j] in gold_phrases and j + 1 < len1:
                good_dialogs[i]['utterances'][j + 1] = ''
            elif any([banned_word in good_dialogs[i]['utterances'][j]
                      for banned_word in banned_words]):
                good_dialogs[i]['utterances'][j] = ''
    return good_dialogs


def main():
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
    parser.add_argument('--blacklist_dir', type=str, default='annotators/BlacklistedWordsDetector/blacklists')
    parser.add_argument('--time_window', type=int, default=30)
    ner_model = build_model(configs.ner.ner_conll2003_bert, download=True)
    args = parser.parse_args()
    assert '_v' in args.output_file, 'Requires version in output'
    assert '_v' in args.bad_output_file, 'Requires version in bad output'
    banned_words = ['my unknown', 'unknown is', 'INTERJECTION']
    for blacklist_file in os.listdir(args.blacklist_dir):
        banned_words1 = [j.strip() for j in open(args.blacklist_dir + '/' + blacklist_file, 'r').readlines()]
        banned_words = banned_words + banned_words1
    gold_phrases = open(args.gold_phrase_file, 'r').readlines()[1:]
    gold_list = ['yes', 'no']
    for gold_phrase in gold_phrases:
        gold_phrase = gold_phrase.strip()
        if gold_phrase[0] == '"':
            gold_phrase = gold_phrase[1:]
        gold_phrase = gold_phrase.split('"\n')[0].split('" "')[0].lower()
        if '"' in gold_phrase:
            gold_phrase = gold_phrase[:gold_phrase.find('"')]
        print(gold_phrase)
        gold_list.append(gold_phrase)
    old_output_file = args.output_file
    while os.path.exists(increment(old_output_file)):
        old_output_file = increment(old_output_file)
    try:
        good_dialogs = json.load(open(old_output_file, 'r'))
        good_dialogs = filter_gold(good_dialogs, gold_list, banned_words)
        output_file = increment(old_output_file)
    except BaseException:
        print('No previous output file found')
        good_dialogs = []
        output_file = old_output_file
    print('Number of good dialogs read from file: ' + str(len(good_dialogs)))
    utts1 = []
    for gold_phrase in gold_list:
        for _ in range(10):
            utts1.append(gold_phrase)
            utts1.append('')
    bad_ids, bad_output_file = None, None
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
    print('Number of bad dialogs read from file: ' + str(len(bad_dialogs)))
    assert bad_output_file is not None
    for i in range(len(good_dialogs)):
        if 'conversation_id' in good_dialogs[i]:
            good_dialogs[i]['id'] = good_dialogs[i]['conversation_id']
            del good_dialogs[i]['conversation_id']
    used_good_ids = set([dialog['id'] for dialog in good_dialogs])
    used_bad_ids = set([dialog['id'] for dialog in bad_dialogs])
    print('Reading ratings from file ' + str(args.ratings_file))
    ratings = pd.read_csv(args.ratings_file)
    good_ratings = ratings[ratings['Rating'] >= 5]
    good_ids = set(list(good_ratings['Conversation ID']))
    if args.bad_output_file:
        bad_ratings = ratings[ratings['Rating'] <= 3]
        bad_ids = set(list(bad_ratings['Conversation ID']))
        assert bad_ids is not None
    print('Reading dialogs from file ' + str(args.dialogs_file))
    dialogs = json.load(open(args.dialogs_file, 'r'))
    print('Total number of all dialogs: ' + str(len(dialogs)))
    print('Total number of good dialogs: ' + str(len(good_ids)))
    print('Total number of bad dialogs: ' + str(len(bad_ids)))
    dialogs = [j for j in dialogs if 'conversation_id' in j['utterances'][0]['attributes']]
    for i in range(len(dialogs)):
        dialogs[i]['id'] = dialogs[i]['utterances'][0]['attributes']['conversation_id']
    assert len(dialogs) > 0
    last_dialog_ids = set()
    for dialog in dialogs:
        date_info = dialog['utterances'][0]['date_time'][:10]
        date = datetime.datetime.strptime(date_info, '%Y-%M-%d')
        not_long_ago = (datetime.datetime.now() - date).days < args.time_window
        if not_long_ago:
            last_dialog_ids.add(dialog['id'])
    print('Time window for good dialogs: ' + str(args.time_window) + ' DAYS')
    print('Number of dialogs in this window: ' + str(len(last_dialog_ids)))
    all_good_dialogs = [dialog for dialog in dialogs
                        if all([dialog['id'] in last_dialog_ids,
                                dialog['id'] in good_ids,
                                len(dialog['utterances']) >= 5])]
    print('Total number of good dialogs in this window: ' + str(len(all_good_dialogs)))
    all_bad_dialogs = [dialog for dialog in dialogs if dialog['id'] in bad_ids]
    print('Total number of bad dialogs: ' + str(len(all_bad_dialogs)))
    new_bad_dialogs = [dialog for dialog in all_bad_dialogs
                       if dialog['id'] not in used_bad_ids]
    print('Total number of new bad dialogs: ' + str(len(new_bad_dialogs)))
    new_good_dialogs = [dialog for dialog in all_good_dialogs
                        if dialog['id'] not in used_good_ids]
    print('Total number of new good dialogs: ' + str(len(new_bad_dialogs)))
    new_good_dialogs = [process(dialog, gold_list, banned_words, ner_model)
                        for dialog in tqdm(new_good_dialogs)]
    new_bad_dialogs = [process(dialog, gold_list, banned_words, ner_model=None)
                       for dialog in tqdm(new_bad_dialogs)]
    good_dialogs = good_dialogs + new_good_dialogs
    bad_dialogs = bad_dialogs + new_bad_dialogs
    good_dialogs = good_dialogs + [{'id': 0, 'utterances': utts1}]
    json.dump(good_dialogs, open(output_file, 'w'), indent=4)
    json.dump(bad_dialogs, open(bad_output_file, 'w'), indent=4)
    print('Dialogs successfully extracted into file ' + str(output_file))
    print('Bad dialogs successfully extracted into file ' + str(bad_output_file))


main()
