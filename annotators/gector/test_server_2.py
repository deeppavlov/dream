# flake8: noqa
#
##########################################################################
# Attention, this file cannot be changed, if you change it I will find you#
##########################################################################
#
import argparse
import json
import os
import time

from flask import jsonify

import requests
# from cp_tests import utils

SEED = 31415
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 2102))
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknow_skill")
TEST_DATA_DIR = os.getenv("TEST_DATA_DIR", "test_data")


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--rewrite_ground_truth", action="store_true", default=False)
args = parser.parse_args()


def test_skill(rewrite_ground_truth):
    url = f"http://0.0.0.0:{SERVICE_PORT}/model"

    
    # request = {
    #     "input_data": [
    #         {
    #             "annotations": {
    #                 "basic_reader": {
    #                     "extended_markup": {
    #                         "clear_essay_sentences": [
    #                             [
    #                                 {
    #                                     "text": "He have lose his luggage at the airport.",
    #                                     "words": [
    #                                         "He",
    #                                         "have",
    #                                         "lose",
    #                                         "his",
    #                                         "luggage",
    #                                         "at",
    #                                         "the",
    #                                         "airport",
    #                                         "."
    #                                     ]
    #                                 }
    #                             ],
    #                         ],
    #                         "clear_essay_word_offsets": [
    #                             [
    #                                 [
    #                                     0,
    #                                     3,
    #                                     8,
    #                                     13,
    #                                     17,
    #                                     25,
    #                                     28,
    #                                     32,
    #                                     39
    #                                 ]
    #                             ]
    #                             ]
    #                             },
    #                             "standard_markup": {
    #                                 "criteria": {
    #                                 "K1": "0",
    #                                 "K2": "0",
    #                                 "K3": "0",
    #                                 "K4": "0",
    #                                 "K5": "0"
    #                                 },
    #                                 "fileName": "0050089_exp104.json",
    #                                 "meta": {
    #                                 "category": "",
    #                                 "class": "1 курс",
    #                                 "id": "0050089",
    #                                 "name": "0050089_en_What_is_the_best_way_to_protect_yourself_from_getting_infected_by_the_coronavirus_noexp.txt",
    #                                 "subject": "eng",
    #                                 "taskText": "",
    #                                 "test": "эссе тренировка",
    #                                 "theme": "What is the best way to protect yourself from getting infected by the coronavirus.",
    #                                 "uuid": "a6cabee9-5083-4e34-bc9d-fe285eaf898f",
    #                                 "year": 2020
    #                                 },
    #                                 "selections": [
    #                                     {}
    #                                 ],
    #                                 "text": "At present all of humanity is quarantined due to the coronavirus. This virus has caused a lot of problems in people. And I will answer one of them in my essay. What is the best way to protect yourself from getting infected by the coronavirus?\nTo begin, I’ll tell you, how this virus can infect. COVID-19 can be infected from a person infected with the virus. The disease is transmitted mainly from person to person through small droplets secreted by the infected COVID-19 from the nose or mouth when coughing, sneezing or talking.\nTo protect yourself from coronavirus infection, you should regularly treat your hands with an alcohol-containing product or wash them with soap, if possible. If a virus is present on the surface of the hands, then treating it with such a product or washing with soap will kill it. Keeping a distance of at least one meter is also necessary, because a person can breathe in drops released from the nose or mouth of another person who may be sick with this very virus. Many people often touch their faces, rub their eyes. And you can’t do this, since we often touch with our hands different objects that the virus could get into. and I think, it’s clear that the contacts with people needs to be limited.\nThus, in order to protect yourself from coronavirus infection, it is necessary to perform a number of these basic measures."
    #                                 }
    #                                 },
    #                                 "contraction_corrector": {
    #                                     "essay_sentences": [
    #                                         [
    #                                             {
    #                                                 "text": "He have lose his luggage at the airport.",
    #                                                 "words": [
    #                                                     "He",
    #                                                     "have",
    #                                                     "lose",
    #                                                     "his",
    #                                                     "luggage",
    #                                                     "at",
    #                                                     "the",
    #                                                     "airport",
    #                                                     "."
    #                                                 ]
    #                                             }
    #                                         ]
    #                                     ],
    #                                     "index_map": [
    #                                         [
    #                                             [
    #                                                 0,
    #                                                 3,
    #                                                 8,
    #                                                 13,
    #                                                 17,
    #                                                 25,
    #                                                 28,
    #                                                 32,
    #                                                 39
    #                                             ]
    #                                         ]
    #                                     ],
    #                                     "selections": [
    #                                         {
    #                                             "correction": "I will",
    #                                             "endSelection": 257,
    #                                             "startSelection": 253
    #                                         }
    #                                     ]
    #                                 }
    #                             }
    #                         }
    #                     ]
    #                 }

    

    request = {
        "input_data": [
            {
                "annotations": {
                    "basic_reader": {
                        "standard_markup": {
                            "text": "He have lose his luggage at the airport."
                        },
                        "extended_markup": {
                            "clear_essay_sentences": [
                                [
                                    {
                                        "text": "He have lose his luggage at the airport.",
                                        "words": [
                                            "He",
                                            "have",
                                            "lose",
                                            "his",
                                            "luggage",
                                            "at",
                                            "the",
                                            "airport",
                                            "."
                                        ]
                                    }
                                ]
                            ],
                            "clear_essay_word_offsets": [
                                [
                                    [
                                        0,
                                        3,
                                        8,
                                        13,
                                        17,
                                        25,
                                        28,
                                        32,
                                        39
                                    ]
                                ]
                            ]
                        }
                    },
                    "contraction_corrector": {
                        "essay_sentences": [
                            [
                                {
                                    "text": "He have lose his luggage at the airport.",
                                    "words": [
                                        "He",
                                        "have",
                                        "lose",
                                        "his",
                                        "luggage",
                                        "at",
                                        "the",
                                        "airport",
                                        "."
                                    ]
                                }
                            ]
                        ],
                        "index_map": [
                            [
                                [
                                    0,
                                    1,
                                    2,
                                    3,
                                    4,
                                    5,
                                    6,
                                    7,
                                    8,
                                    9
                                ]
                            ]
                        ]
                    }
                },
                "instance_info": {
                    "subject": "eng"
                }
            }
        ]
    }
    response = requests.post(url, json=request, timeout=180).json()[0]
    # response = requests.post(url, json=request, timeout=180).json()
    # print(jsonify(response))
    # total_time = time.time() - st_time
    # print(f"exec time: {total_time:.3f}s")
    json_object = json.dumps(response, indent=4)
    with open("sample_gector.json", "w") as outfile:
        outfile.write(json_object)
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill(args.rewrite_ground_truth)
