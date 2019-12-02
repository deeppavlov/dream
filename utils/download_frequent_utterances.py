from datetime import date, timedelta
import os

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output', help='folder to write results', default='./ratings')
parser.add_argument('--start_date', help='stat was initially collected from start_date', default='2019-10-10')
parser.add_argument('--end_date', help='to end_date', default='2019-11-08')


# USAGE:
# to use this script you have to configure aws cli by running `aws configure`
# python utils/download_frequent_utterances.py --output ./ratings

if __name__ == '__main__':
    args = parser.parse_args()
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    today = date.today()
    week = timedelta(days=7)

    cmd = 'aws s3 cp s3://alexaprize/807746935730/FrequentUtterances/FrequentUtterances_{}_{}.txt\
        ./{}/frequent_utterances/'

    while end_date <= today:
        os.system(cmd.format(start_date.isoformat(), end_date.isoformat(), args.output))
        end_date = end_date + week
        start_date = start_date + week
