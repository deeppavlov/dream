import requests
import time
import sentry_sdk
from sys import argv
from os import getenv


def main(url, interval=600):
    user_id = "status_monitoring_user"
    while(True):
        result = requests.post(url, json={"user_id": user_id, "payload": "hey"}).json()
        assert len(result['response']) > 1
        assert result['user_id'] == user_id
        time.sleep(interval)


sentry_sdk.init(getenv('SENTRY_DSN'))
if __name__ == '__main__':
    main(argv[1])
