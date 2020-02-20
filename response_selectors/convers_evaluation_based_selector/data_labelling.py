# USAGE example: python response_selectors/convers_evaluation_based_selector/data_labelling.py  \
#                 --dialog_id 5e412fabd655fa53fa6bc9f8 \
#                 --save_dir response_selectors/convers_evaluation_based_selector/labeled_data/
import requests
import json
import argparse
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--dialog_id', help='dialog id to label')
parser.add_argument('--save_dir', help='directory to save labeled data')


def get_dialog_data(dialog_id):
    prod_url = "http://docker-externalloa-lofsuritnple-525614984.us-east-1.elb.amazonaws.com:4242/api/dialogs"
    dialog_url = f"{prod_url}/{dialog_id}"
    return requests.get(dialog_url).json()


def prepare_data(dialog_data):
    utterances = list(dialog_data['utterances'])
    rows = []
    for i in range(len(utterances)):
        if utterances[i]['user']['user_type'] == 'bot':
            if i - 1 < 0:
                user_utts = []
                bot_utts = []
                new_utts = utterances[i:i]
            elif i - 2 < 0:
                user_utts = [{"text": utterances[i - 1]['text']}]
                bot_utts = []
                new_utts = utterances[i - 1:i]
            elif i - 4 < 0:
                user_utts = [{"text": utterances[i - 1]['text']}, {"text": utterances[i - 3]['text']}]
                bot_utt = utterances[i - 2]
                bot_utts = [
                    {'text': bot_utt['text'], 'confidence': bot_utt['confidence'],
                     'skill_name': bot_utt['active_skill']}
                ]
                new_utts = utterances[i - 3:i]
            else:
                bot_utt = utterances[i - 2]
                prev_bot_utt = utterances[i - 4]
                user_utts = [{"text": utterances[i - 1]['text']}, {"text": utterances[i - 3]['text']}]
                bot_utts = [
                    {
                        'text': bot_utt['text'], 'confidence': bot_utt['confidence'],
                        'skill_name': bot_utt['active_skill']},
                    {
                        'text': prev_bot_utt['text'], 'confidence': prev_bot_utt['confidence'],
                        'skill_name': prev_bot_utt['active_skill']}
                ]
                new_utts = utterances[i - 4:i]
            hypots = utterances[i - 1]['hypotheses']

            row = {
                'human_utterances': user_utts,
                'bot_utterances': bot_utts,
                'hypotheses': hypots,
                'utterances': new_utts
            }
            rows.append(row)
    return rows


def label_prepared_data(prepared_data):
    try:
        for row in prepared_data:
            for utt in row["utterances"]:
                print(f'{utt["user"]["user_type"]}: {utt["text"]}')
            assert row['utterances'][-1]['user']['user_type'] == 'human'
            sorted_hypots = list(sorted(
                row['utterances'][-1]["hypotheses"], key=lambda x: x["confidence"], reverse=True)
            )
            for i, h in enumerate(sorted_hypots):
                if h['confidence'] > 0:
                    print(f'{i} hypot: {h["text"]}; skill: {h["skill_name"]}; conf: {h["confidence"]}')
            hypot_nums = input("Type best hypot num(s), separated by comma: ")
            if hypot_nums:
                print(f"You selected: {hypot_nums}")
                for hypot_num in hypot_nums.split(","):
                    hypot_num = int(hypot_num.strip())
                    sorted_hypots[hypot_num]['is_best'] = True
                    row['utterances'][-1]["has_is_best"] = True
            else:
                print("You skipped")
            row['utterances'][-1]['hypotheses'] = sorted_hypots
            print()
    except (Exception, KeyboardInterrupt) as e:
        print(f"EXCEPTION!!!!! {e}. Labeled data saving...")
    return prepared_data


def main(dialog_id, labeled_data_dir):
    dialog_data = get_dialog_data(dialog_id)
    prepared_data = prepare_data(dialog_data)
    labeled_data = label_prepared_data(prepared_data)

    with open(f'{labeled_data_dir}/{dialog_id}.json', 'w') as f:
        json.dump(labeled_data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.dialog_id, args.save_dir)
