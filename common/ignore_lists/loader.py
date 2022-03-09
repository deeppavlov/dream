from typing import Union, List

from pathlib import Path


def _load_ignore_list(path: Union[Path, str]) -> List[str]:
    """Load list of ignored words/phrases from file

    Args:
        path: path to .txt file with one word/phrase per line

    Returns: list of non-empty file lines without newline characters (other whitespaces are preserved)

    """
    ignore_list = []

    with open(path, "r", encoding="utf-8") as ignore_f:
        for line in list(ignore_f):
            line = line.strip("\n")
            if line:
                ignore_list.append(line)

    return ignore_list


FALSE_POS_NPS_LIST = _load_ignore_list("common/ignore_lists/false_pos_nps.txt")
BAD_NPS_LIST = _load_ignore_list("common/ignore_lists/bad_nps.txt")
