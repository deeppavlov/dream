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
