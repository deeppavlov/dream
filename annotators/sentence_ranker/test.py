import os
import requests
import json

def test_respond():
    url = "http://0.0.0.0:8130/response"

    # [0]["human_utterances"][-1]["annotations"]['sentseg']['punct_sent']
    test_data = {
        "dialogs": [ 
            {
                "human_utterances": [
                    {
                        "annotations": {
                            "sentseg": {
                                "punct_sent": "Hi. Do you like onions?"
                                
                            }
                        }
                    }
                ]
            },
            {
                "human_utterances": [
                    {
                        "annotations": {
                            "sentseg": {
                                "punct_sent": "My mum working hard. What about you?"
                            }
                        }
                    }
                ]
            },
        ]
    }

    result = requests.post(url, json=test_data).json()
    assert len(result[0][0]) > 0, "Empty response"
    print("Success")


if __name__ == "__main__":
    test_respond()
