import difflib
import json
import pathlib
import os
import logging

logger = logging.getLogger(__name__)


def compare_structs(ground_truth, hypothesis, stack_track="hypothesis", ignored_keys=[]):
    ground_truth = json.loads(json.dumps(ground_truth))
    hypothesis = json.loads(json.dumps(hypothesis))
    if type(ground_truth) != type(hypothesis):
        return (
            False,
            f"path :: {stack_track} :: ground_truth type {type(ground_truth)} != hypothesis type {type(hypothesis)}",
        )
    elif isinstance(ground_truth, dict):
        if set(ground_truth.keys()).symmetric_difference(set(hypothesis.keys())):
            return (
                False,
                f"path :: {stack_track} "
                f":: ground_truth keys ({list(ground_truth.keys())}) != hypothesis keys ({list(hypothesis.keys())})",
            )
        for key in ground_truth.keys():
            if key not in ignored_keys:
                is_equal_flag, msg = compare_structs(
                    ground_truth[key],
                    hypothesis[key],
                    f"{stack_track}[{key}]",
                    ignored_keys,
                )
                if not is_equal_flag:
                    return is_equal_flag, msg
    elif isinstance(ground_truth, list):
        if len(ground_truth) != len(hypothesis):
            return (
                False,
                f"path :: {stack_track} "
                f":: ground_truth len ({len(ground_truth)}) != hypothesis len ({len(hypothesis)})",
            )
        for index, (ground_truth_item, hypothesis_item) in enumerate(zip(ground_truth, hypothesis)):
            is_equal_flag, msg = compare_structs(
                ground_truth_item,
                hypothesis_item,
                f"{stack_track}[{index}]",
                ignored_keys,
            )
            if not is_equal_flag:
                return is_equal_flag, msg
    elif ground_truth != hypothesis:
        return False, f"path :: {stack_track} :: `{ground_truth}` != `{hypothesis}`"
    return True, ""


def compare_text(ground_truth, hypothesis, ratio=0.9):
    res_ratio = difflib.SequenceMatcher(None, ground_truth.split(), hypothesis.split()).ratio()
    return res_ratio >= ratio, res_ratio


def get_tests(postfix):
    return {
        file.name.replace(postfix, ""): json.load(file.open("rt"))
        for file in pathlib.Path("tests/").glob(f"*{postfix}")
    }


def get_dataset():
    in_data = get_tests("_in.json")
    out_data = get_tests("_out.json")
    assert set(in_data) == set(out_data), "All files must be in pairs."
    return in_data, out_data


def save_to_test(data, file_path, indent=4):
    file_path = pathlib.Path(file_path)
    assert "tests" == file_path.parent.name, "Test has to be at `tests` dir"
    assert file_path.name[-8:] in ["_in.json", "out.json"], "file name has to contain _in.json/_out.json"
    json.dump(data, file_path.open("wt"), indent=indent)
    stat = file_path.parent.stat()
    os.chown(file_path, stat.st_uid, stat.st_gid)
