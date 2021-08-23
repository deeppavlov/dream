#!usr/bin/env python3

import json
import os
import requests
import datetime
import argparse
import time
import pysftp
import tarfile


SHARE_HOST_NAME = "share.ipavlov.mipt.ru"
USER_NAME = "dilyara.baymurzina"
PRIVATE_KEY_PATH = "~/.ssh/id_rsa"


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def parse_one_period(SITE, stdate, enddate, mode="posts"):
    docs = dict()
    offset = 0
    count = 100
    while True:
        URL = SITE + "?" + f"stdate={stdate.strftime('%Y/%m/%d')}&" \
                           f"enddate={enddate.strftime('%Y/%m/%d')}&" \
                           f"offset={offset}&count={count}&key={API_KEY}"
        req = requests.request(url=URL, method='GET').json()
        if 'errorMessage' in req.keys():
            if req['errorMessage'] == 'Rate limit exceed':
                time.sleep(15 * 60)
                continue
            else:
                raise Exception(f"Request exception: {req['errorMessage']}")
        else:
            data = req['docs']
        if len(data) == 0:
            filename = f'{mode}_' + stdate.strftime("%Y:%m:%d") + '-' + enddate.strftime("%Y:%m:%d")
            print(f"{mode}: saved in {filename}.json")
            name = ''.join([DATA_PATH, filename, '.json'])
            if os.path.isfile(name):
                prev_docs = json.load(open(name, 'r'))
                for k in prev_docs:
                    # it also removes duplicates!
                    docs[k] = prev_docs[k]
                json.dump(docs, open(name, 'w'), indent=2)
                break
            else:
                json.dump(docs, open(name, 'w'), indent=2)
                break
        else:
            docs.update({news['contenturl']: news for news in data})
            offset += count

    return


API_KEY = "ooUVrKLP1ap5zTjvb7sy"

DOCS_SITE = "https://docs.washpost.com/docs"
COMMENTS_SITE = "https://docs.washpost.com/comments"

parser = argparse.ArgumentParser(description='Washington post crawler')
parser.add_argument('--stopdate', help='stopping date in format %Y/%m/%d', default='2019/09/01')
parser.add_argument('--parse_comments', help='wheather to parse comments or not', type=bool, default=False)
parser.add_argument('--keep_crawling', help='wheather to keep parsing or not', type=bool, default=False)

args = parser.parse_args()

stopdate = datetime.datetime.strptime(args.stopdate, "%Y/%m/%d")
parse_comments = args.parse_comments
keep_crawling = args.keep_crawling

DATA_PATH = './data/'
timedelta = datetime.timedelta(hours=1, minutes=30)  # daily report


if keep_crawling:
    os.chdir("/home/dilyara.baymurzina/wapo/updating/")
    for f in os.listdir("./data/"):
        os.remove("./data/" + f)
    done_today = False
    prev_parsed = datetime.datetime.today() - datetime.timedelta(days=1)
    while True:
        t = datetime.datetime.today()
        if (t - prev_parsed).seconds * 1. / 3600 >= 1.5:
            print("EVERY 1.5 HOURS CRAWLING")
            parse_one_period(DOCS_SITE, stdate=t - timedelta, enddate=t, mode="posts")

            with pysftp.Connection(host=SHARE_HOST_NAME, username=USER_NAME,
                                   private_key=PRIVATE_KEY_PATH) as sftp:
                local_file = "updated_washington_post_data.tar.gz"
                make_tarfile(local_file, DATA_PATH)
                remote_file = "/home/export/alexaprize_data/updated_washington_post_data.tar.gz"
                sftp.put(local_file, remote_file)
            if parse_comments:
                parse_one_period(COMMENTS_SITE, stdate=t - timedelta, enddate=t, mode="comments")
        time.sleep(timedelta.seconds)
else:
    os.chdir("/home/dilyara.baymurzina/wapo/get_period/")
    for f in os.listdir("./data/"):
        os.remove("./data/" + f)
    enddate = datetime.datetime.today()
    stdate = enddate - timedelta
    stopdate = datetime.datetime(year=2019, month=11, day=13)
    while enddate > stopdate:
        parse_one_period(DOCS_SITE, stdate, enddate, mode="posts")
        if parse_comments:
            parse_one_period(COMMENTS_SITE, stdate, enddate, mode="comments")
        enddate = stdate
        stdate = enddate - timedelta

    with pysftp.Connection(host=SHARE_HOST_NAME, username=USER_NAME,
                           private_key=PRIVATE_KEY_PATH) as sftp:
        local_file = "washington_post_data.tar.gz"
        make_tarfile(local_file, DATA_PATH)
        remote_file = "/home/export/alexaprize_data/washington_post_data.tar.gz"
        sftp.put(local_file, remote_file)
