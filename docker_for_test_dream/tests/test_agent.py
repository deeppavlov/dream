#!/usr/bin/env python

import requests
import json
from os import getenv

request_data = [{"user_id":"xyz","payload":"Hello"},
                {"user_id":"xyz","payload":"turn clockwise right now"},
                {"user_id":"xyz","payload":"You must move forward"},
                {"user_id":"xyz","payload":"You must move forward 10 metres"},
                {"user_id":"xyz","payload":"move forward 10 metres"},
                {"user_id":"xyz","payload":"detect this people"},
                {"user_id":"xyz","payload":"detect this car"},
                ]

def main_test():
    url = "http://0.0.0.0:4242"
    # url = "http://localhost:4242"
    
    print('=========')
    for cur_request in request_data:
        r = requests.post(url=url, json=cur_request)
        print('Request - ', cur_request['payload'], '\n', 'Response - ', r.json()['response'])
        print('============')


if __name__ == "__main__":
    main_test()
