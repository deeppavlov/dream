#!/usr/bin/env python

import requests


def main_test():

    # url = "http://0.0.0.0:4343/tts?user_id=fdgdfgsd"
    url = "http://0.0.0.0:4343/tts?text=kill_mankind"
    # url = "http://http://10.11.1.41:4242/tts?text=kill_mankind"

    # url = "http://localhost:4242/tts?text=kill_mankind"

    # "http://_tts_service_name:_tts_service_port_/tts?text=_your_text_here_"
    # text = "уничтожить человеков"
    r = requests.post(url)

    # r = requests.post(url, files={'text': text})

    print(r)


if __name__ == "__main__":
    main_test()
