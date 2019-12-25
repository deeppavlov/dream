# USAGE example: python utils/collect_amazon_dialogs.py --input dialogs.json
# USAGE example with requesting: python utils/collect_amazon_dialogs.py --input dialogs.json --with_debug_info \
#        --with_requesting --url http://Docker-st-External-1918W05RU8XQW-178993125.us-east-1.elb.amazonaws.com:4242
# to get ratings run ./utils/download_ratings.sh
# to get dialogs run wget <agent_url>:4242/dialogs
import os
import json
import pandas as pd
import sys
import argparse
import logging
import asyncio
import uuid
import aiohttp
from tqdm import tqdm
from http_api_test import perform_test_dialogue

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--input', help='input json or folder with dialogs (can be fetched through /dialogs)')
parser.add_argument('--output', help='output filename prefix', default='amazon_dialogs')
parser.add_argument('--with_requesting', action='store_true', default=False, help='pass user queries to url')
parser.add_argument('--with_debug_info', action='store_true', default=False,
                    help='get debug info for with_requesting mode')
parser.add_argument('--with_skill_name', action='store_true', default=False,
                    help='get active skill name for collected dialogs')
parser.add_argument('--url', help='url, used only when with_requesting is True', default='http://0.0.0.0:4242')
parser.add_argument('--feedback', help='feedbacks csv', default='./ratings/conversation_feedback.csv')
parser.add_argument('--ratings', help='ratings csv', default='./ratings/ratings.csv')
parser.add_argument('--first_n', help='Number of dialogs for debug', default=999999)


def print_pretty(dialog, file=sys.stdout, field='dialog', with_debug_info=False, with_skill_name=False):
    # Skip /start and next utt
    # TODO: Do not use 2:, for new dialogs, because /start not saved in state in new version of dp-agent
    if with_debug_info:
        bot_idx = -2
        human_idx = -3
    else:
        bot_idx = -1
        human_idx = -2

    if field == 'new_dialog':
        print(dialog)
        for utt in dialog:
            bot_response = utt[bot_idx]
            human_response = utt[human_idx]
            if bot_response != 'command_performed':
                print(f"Human: {human_response}", file=file)
                print(f"Bot: {bot_response}", file=file)
                if with_debug_info:
                    for row in utt[-1]["debug_output"]:
                        print(f"Bot {row['skill_name']} ({row['confidence']}): {row['text']}", file=file)
    else:
        for i, utt in enumerate(dialog['utterances']):
            person = 'Bot' if i % 2 == 1 else 'Human'
            if with_skill_name and person == 'Bot':
                active_skill = utt.get('active_skill', 'no_skill_name')
                print(f"{person}({active_skill}): {utt['text']}", file=file)
            else:
                print(f"{person}: {utt['text']}", file=file)


def collect_human_responses(dialog):
    responses = []
    for i, utt in enumerate(dialog['utterances']):
        if i % 2 != 1:
            responses.append(utt['text'])
    return responses


def print_row(row, f, field='dialog', with_debug_info=False, with_skill_name=False):
    print(f'--{row["conversation_id"]}----{row["rating_val"]}----{row["feedback_txt"]}---{row["start_time"]}',
          file=f)
    print_pretty(row[field], file=f, field=field, with_debug_info=with_debug_info, with_skill_name=with_skill_name)
    print("-----------------------", file=f)


def print_to_file(new_conversations, args):
    no_feedbacks = []
    with_feedbacks = []
    with open(f'./{args.output}_all.txt', 'w') as f:
        for _, row in new_conversations.sort_values('start_time', ascending=False).iterrows():
            if row["feedback_txt"] == 'no_feedback':
                no_feedbacks.append(row)
            else:
                with_feedbacks.append(row)
            print_row(row, f, with_skill_name=args.with_skill_name)

    with open(f'./{args.output}_with_feedbacks.txt', 'w') as f:
        for row in with_feedbacks:
            print_row(row, f, with_skill_name=args.with_skill_name)

    with open(f'./{args.output}_without_feedbacks.txt', 'w') as f:
        for row in no_feedbacks:
            print_row(row, f, with_skill_name=args.with_skill_name)

    if args.with_requesting:
        with open(f'./{args.output}_with_requests.txt', 'w') as f:
            for _, row in new_conversations.sort_values('start_time', ascending=False).iterrows():
                print_row(row, f, 'new_dialog', with_debug_info=args.with_debug_info)


async def make_requests(new_conversations, args):
    result = []
    async with aiohttp.ClientSession() as session:
        for _, row in tqdm(new_conversations.iterrows(), total=new_conversations.shape[0]):
            uid = uuid.uuid4().hex
            dialog = row["dialog"]
            responses = collect_human_responses(dialog)
            inp = ['/start'] + responses + ['/close']
            res = await perform_test_dialogue(session, args.url, uid, inp, args.with_debug_info)
            result.append(res)
    new_conversations["new_dialog"] = result
    return new_conversations


async def main(args):
    if os.path.isfile(args.input):
        with open(args.input, 'r') as f:
            data = json.load(f)
    else:
        data = []
        for filename in os.listdir(args.input):
            path = os.path.join(args.input, filename)
            with open(path, 'r') as f:
                dialog_list = json.load(f)
            data.extend(dialog_list)
    conversations = {}
    for d in data:
        for utt in d['utterances']:
            if "conversation_id" in utt.get("attributes", {}):
                conversation_id = utt["attributes"]["conversation_id"]
                conversations[conversation_id] = d
    feedback = pd.read_csv(args.feedback)
    ratings = pd.read_csv(args.ratings)

    new_conversations = []
    for conv_id, dialog in conversations.items():
        feedback_txt = feedback[feedback['conversation_id'] == conv_id]
        if len(feedback_txt):
            feedback_txt = feedback_txt['feedback'].iloc[0]
        else:
            feedback_txt = 'no_feedback'
        rating_val = ratings[ratings['Conversation ID'] == conv_id]
        if len(rating_val):
            start_time = rating_val['Approximate Start Time'].iloc[0]
            rating_val = rating_val['Rating'].iloc[0]
            new_conversations.append({"conversation_id": conv_id, "rating_val": float(rating_val),
                                      "feedback_txt": feedback_txt, "dialog": dialog,
                                      "start_time": start_time})

    if len(new_conversations) > 0:
        new_conversations = pd.DataFrame(new_conversations)
        new_conversations['start_time'] = pd.to_datetime(new_conversations['start_time'])
        new_conversations = new_conversations.sort_values('start_time', ascending=False)
        args.first_n = int(args.first_n)
        new_conversations = new_conversations.head(args.first_n)
        if args.with_requesting:
            new_conversations = await make_requests(new_conversations, args)
        print_to_file(new_conversations, args)


if __name__ == '__main__':
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main(args))
    loop.run_until_complete(future)
