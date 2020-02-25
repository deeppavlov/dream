import boto3
import os
from tqdm import tqdm
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--bucket', help='bucket name', default='alexa-prod-dialogs-dumps')
parser.add_argument('--output', help='path to download dumps', default='./dialogs_dumps')
parser.add_argument('--output_txt', action='store_true', default=False)
parser.add_argument('--output_txt_path', help='path to dialogs in txt format', default='./dialogs_dumps_txt')
parser.add_argument('--dp_agent_alexa_path', help='path to dp-agent-alexa project folder', default='.')


def get_local_files(folder):
    if os.path.isdir(folder):
        return os.listdir(folder)
    os.makedirs(folder, exist_ok=True)
    return []


if __name__ == '__main__':
    """
    This script will download all dialogs dumps from s3 bucket.
    In case if folder with dumps already exists it downloads only new dumps.

    If output_txt is set also adds dumps in txt format to output_txt_path folder.
    """
    args = parser.parse_args()
    bucket_name = args.bucket
    dump_folder = args.output

    s3_client = boto3.client('s3')
    bucket = boto3.resource('s3').Bucket(bucket_name)

    bucket_filenames = set([el.key for el in bucket.objects.all()])

    local_filenames = set(get_local_files(dump_folder))

    new_files = bucket_filenames - local_filenames
    if len(new_files) == 0:
        print('Dumps already up to date...')
    else:
        for filename in tqdm(bucket_filenames - local_filenames):
            print(filename)
            s3_client.download_file(bucket_name, filename, dump_folder + '/' + filename)
    print('Downloading done')

    if args.output_txt:
        local_filenames = get_local_files(args.output_txt_path)
        bucket_dates = set([el.replace('time_interval_logs_', '').replace('.json', '') for el in bucket_filenames])
        local_dates = [
            el.replace('_all.txt', '').replace('_with_feedbacks.txt', '').replace('_without_feedbacks.txt', '') for el
            in local_filenames]
        # recreate txt dumps for last 48h (because ratings file could be updated with delay)
        local_dates = set(sorted(local_dates)[:-48])
        for date in tqdm(bucket_dates - local_dates):
            dump_filename = f'time_interval_logs_{date}.json'
            cmd = f"{sys.executable} {args.dp_agent_alexa_path}/utils/collect_amazon_dialogs.py --input " \
                f"{dump_folder + '/' + dump_filename} --output {args.output_txt_path + '/' + date}" \
                " --with_skill_name --with_no_rating"
            os.system(cmd)
