from typing import List

CMDS = ["/new_persona"]


def exclude_cmds(utter: str, cmds: List):
    if cmds:
        utter = utter.replace(cmds[-1], "")
        return exclude_cmds(utter, cmds[:-1])
    else:
        return utter


def commands_excluder(utters_batch: List, cmds: List = []):
    cmds = cmds if cmds else CMDS
    out_batch = []
    for utters in utters_batch:
        out_batch.append([exclude_cmds(ut, cmds) for ut in utters])
    return out_batch
