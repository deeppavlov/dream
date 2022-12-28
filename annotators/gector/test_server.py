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

import requests

import pathlib
import re


def compare_structs(ground_truth, hypothesis, stack_track="hypothesis"):
    if type(ground_truth) != type(hypothesis):
        return (
            False,
            f"path :: {stack_track} :: ground_truth type {type(ground_truth)} != hypothesis type {type(hypothesis)}",
        )
    if isinstance(ground_truth, dict):
        if set(ground_truth.keys()).symmetric_difference(set(hypothesis.keys())):
            return (
                False,
                f"path :: {stack_track} "
                f":: ground_truth keys ({list(ground_truth.keys())}) != hypothesis keys ({list(hypothesis.keys())})",
            )
        for key in ground_truth.keys():
            is_equal_flag, msg = compare_structs(ground_truth[key], hypothesis[key], f"{stack_track}[{key}]")
            if not is_equal_flag:
                return is_equal_flag, msg
    if isinstance(ground_truth, list):
        if len(ground_truth) != len(hypothesis):
            return (
                False,
                f"path :: {stack_track} "
                f":: ground_truth len ({len(ground_truth)}) != hypothesis len ({len(hypothesis)})",
            )
        for index, (ground_truth_item, hypothesis_item) in enumerate(zip(ground_truth, hypothesis)):
            is_equal_flag, msg = compare_structs(ground_truth_item, hypothesis_item, f"{stack_track}[{index}]")
            if not is_equal_flag:
                return is_equal_flag, msg
    if ground_truth != hypothesis:
        return False, f"path :: {stack_track} :: `{ground_truth}` != `{hypothesis}`"
    return True, ""


input_reg = re.compile("_input.*")
output_reg = re.compile("_output.*")


def get_data(data_dir="test_data"):
    data_dir = pathlib.Path(data_dir)
    input_files = [file for file in data_dir.glob("./*_input.json")]
    output_files = [file.parent / str(file.name).replace("_input.json", "_output.json") for file in input_files]
    return list(zip(input_files, output_files))


SEED = 31415
# SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3000))
# SERVICE_NAME = os.getenv("SERVICE_NAME", "unknow_skill")
# TEST_DATA_DIR = os.getenv("TEST_DATA_DIR", "test_data")
SERVICE_PORT = 2102
SERVICE_NAME = "gector"
TEST_DATA_DIR = "/home/kpetyxova/prochtenie/services/solvers/gector/test_data"


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--rewrite_ground_truth", action="store_true", default=False)
args = parser.parse_args()


def test_skill(rewrite_ground_truth):
    url = f"http://0.0.0.0:{SERVICE_PORT}/model"
    warnings = 0

    for request_file, response_file in get_data(TEST_DATA_DIR):
        request = json.load(request_file.open())
        print(request_file)
        create_response_file_flag = not response_file.exists()
        st_time = time.time()
        time.sleep(3)
        response = requests.post(url, json=request, timeout=180).json()[0]
        time.sleep(3)
        print(f"cand = {response}")
        total_time = time.time() - st_time
        print(f"exec time: {total_time:.3f}s")
        if create_response_file_flag or rewrite_ground_truth:
            json.dump(response, response_file.open("wt"), ensure_ascii=False, indent=4)
            uid, gid = request_file.stat().st_uid, request_file.stat().st_gid
            os.chown(str(response_file), uid, gid)
            is_equal_flag, msg = False, "New output file is created"
        else:
            is_equal_flag, msg = compare_structs(json.load(response_file.open()), response)
        if not is_equal_flag:
            print("----------------------------------------")
            print(f"cand = {response}")
            print(msg)
            print(f"request_file = {request_file}")
            print(f"response_file = {response_file}")
            warnings += 1
    assert warnings == 0
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill(args.rewrite_ground_truth)
