import json
import argparse
import pathlib
import datetime


parser = argparse.ArgumentParser()
parser.add_argument("-m", "--meta_data", type=pathlib.Path)
args = parser.parse_args()


try:
    data = json.load(args.meta_data.open())
    last_update = data["LastModified"]
    last_update = datetime.datetime.fromisoformat(last_update)
    last_update = last_update.replace(tzinfo=None)
    now = datetime.datetime.now()
    assert (now - last_update) < datetime.timedelta(hours=8), "db is outdated"
    exit(0)
except Exception as exc:
    print(exc)
    exit(1)
