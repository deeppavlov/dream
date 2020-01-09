from core.db import DataBase
from datetime import datetime, timedelta
from core.state_schema import Dialog
import argparse
import json
import boto3
import asyncio
import io
import os

# How to use:
# 1) write bash script, which run this python script with arguments. For example:
# #!/bin/bash
# PYTHONPATH=/<python_path> python /<path_to_this_file> \
# --host=hostname \
# --port=27017 \
# --name=db_name \
# --delta=time interval in hours \
# --date_finish=finish of the time interval, for example - "25/11/19 17:14:41" \
# --bucket_name=name of the bucket \
# 2) docker with cron https://habr.com/ru/company/redmadrobot/blog/305364/
# 3) to run script in cron - just write in command shell 'crontab -e'
# and then, write something like this:
# SHELL=/bin/bash
# PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
# 01 15 * * * /path_to_your_script
# it means, that script gonna work every day in 15:01.
# If you want to run it every hour in hh:05 minutes - write 05 * * * * /path_to_your_script

S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')


def dialogue_to_dict(dialog):
    """
    Returns: dict of dialogue in chosen time interval
    converts Dialogue object to dict
    """
    result = {
        'id': dialog.id,
        'utterances': [],
        'human': dialog.human.to_dict(),
        'bot': dialog.bot.to_dict(),
        'date_start': str(dialog.date_start),
        'date_finish': str(dialog.date_finish)
    }
    for i in dialog.utterances:
        utt_dct = {'text': i.text, 'date_time': str(i.date_time)}
        if hasattr(i, 'attributes'):
            # do not output ASR results in /dialogs
            utt_dct['attributes'] = {k: v for k, v in i.attributes.items() if k != 'speech'}
        if hasattr(i, 'active_skill'):
            utt_dct['active_skill'] = i.active_skill
        result['utterances'].append(utt_dct)
    return result


async def db_to_json(db, date_start, date_finish):
    """reads in time interval from finish_date-delta to finish_date database from database."""
    all_results = []
    async for dialogue in Dialog.get_all_gen(db, date_start, date_finish):
        all_results.append(dialogue_to_dict(dialogue))
    file_name = (f'time_interval_logs_{str(date_start.strftime("%Y.%m.%d_%H:%M"))}-'
                 f'{str(date_finish.strftime("%Y.%m.%d_%H:%M"))}.json')
    file = io.StringIO()
    file.write(json.dumps(all_results))
    #  after writing a file current position is in the end of file. Move it to the first byte of the file
    #  for using read() later.
    file.seek(0)
    return file_name, file


def download_from_s3(bucket_name, file_name_in_s3, file_path, make_json_file_pretty=True):
    """
    downloading file and if it is json file - can make it pretty
    :bucket_name: name of the bucket in amazon-s3-bucket
    :file_name_in_s3: name of the file in this bucket
    :file_path: path, where to save downloaded file
    :make_json_file_pretty: if you want to read your json file by your eyes - this parameter should be True:)
    """
    s3 = boto3.resource('s3', aws_access_key_id=S3_ACCESS_KEY,
                        aws_secret_access_key=S3_SECRET_ACCESS_KEY)
    s3.Bucket(bucket_name).download_file(file_name_in_s3, file_path)
    if make_json_file_pretty:
        with open(file_path, 'r') as f:
            data = json.load(f)
        # Writing JSON data
        with open(file_path, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4)


def write_files(file, file_name, path):
    """write file on disk"""
    with open(path + '/' + file_name, 'w') as fout:
        fout.write(file.read())


def write_files_s3(file, file_name, bucket_name):
    """writes json_file to the amazon-s3-bucket"""
    s3 = boto3.resource('s3', aws_access_key_id=S3_ACCESS_KEY,
                        aws_secret_access_key=S3_SECRET_ACCESS_KEY)
    s3.Bucket(bucket_name).put_object(Key=file_name, Body=file.read())


def valid_date(s):
    """function for arg parse datetime objects"""
    try:
        return datetime.strptime(s, '%d/%m/%y %H:%M:%S')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def get_start_finish_timestamps(date_finish, delta):
    """returns: date_start, date_finish with type datetime"""
    if date_finish is None:
        date_finish = datetime.now()
    date_start = date_finish - timedelta(hours=delta)
    return date_start, date_finish


def main():
    #  parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="localhost", type=str, required=True,
                        help="db host")
    parser.add_argument('--port', default=27017, type=int, required=True,
                        help="db port")
    parser.add_argument('--name', default="dp_agent", type=str, required=True,
                        help="db name")
    parser.add_argument('--delta', default=1, type=int,
                        help="start date is finish date - delta. Length of time interval in hours")
    parser.add_argument("--date_finish", default=None, type=valid_date,
                        help="take data from date_finish format dd/mm/yy hh:mm:ss. example 25/11/19 17:14:41")
    parser.add_argument('--path_to_save', default=None, type=str, help="path to save or name of s3 bucket")
    parser.add_argument('--upload_to_s3', action='store_true', default=False, help='use this flag to upload to s3')
    args = parser.parse_args()

    if args.path_to_save is None:
        msg = 'path_to_save argument is not set'
        raise argparse.ArgumentTypeError(msg)

    #  creating database object
    db = DataBase(args.host, args.port, args.name).get_db()
    date_start, date_finish = get_start_finish_timestamps(date_finish=args.date_finish, delta=args.delta)
    loop = asyncio.get_event_loop()
    #  get io file with data from database in time interval from date_start to date_finish
    file_name, file = loop.run_until_complete(db_to_json(db, date_start, date_finish))
    #  upload file to s3-bucket
    if args.upload_to_s3:
        print(f"Uploading to S3 {args.path_to_save}: {file_name}")
        write_files_s3(file, file_name, bucket_name=args.path_to_save)
    else:
        print(f"Writing on disk to {args.path_to_save}: {file_name}")
        write_files(file, file_name, args.path_to_save)


if __name__ == "__main__":
    main()
