from datetime import date, timedelta
import os

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output', help='folder to write results', default='./ratings')
parser.add_argument('--start_date', help='first date when stat was collected', default='2019-11-09')

# USAGE:
# to use this script you have to configure aws cli by running `aws configure`
# python utils/download_conversation_assessment.py --output ./ratings

if __name__ == '__main__':
    args = parser.parse_args()
    today = date.today()
    week = timedelta(days=7)
    t = date.fromisoformat(args.start_date)
    cmd = 'aws s3 cp s3://alexaprize/807746935730/ConversationAssessments/conversation_assessment_{}.csv\
        ./{}/conversation_assessment/'

    while t <= today:
        os.system(cmd.format(t.isoformat(), args.output))
        t = t + week
