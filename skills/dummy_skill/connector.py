#!/usr/bin/env python

import asyncio
import json
import logging
import time
from copy import deepcopy
from os import getenv
from random import choice
import re
from typing import Callable, Dict

import sentry_sdk


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))

FALLBACK_FILE = getenv("FALLBACK_FILE", "fallbacks_dream_en.json")
DUMMY_DONTKNOW_RESPONSES = json.load(open(f"common/fallbacks/{FALLBACK_FILE}", "r"))

FALLBACK_TO_DOCS_FILE = getenv("FALLBACK_TO_DOCS_FILE", "fallbacks_sentius_en_docs.json")
DUMMY_DOCS_RESPONSES = json.load(open(f"common/fallbacks/{FALLBACK_TO_DOCS_FILE}", "r"))

COMMAND_RESPONSE_MAPPING = {}

HELP_FILE = getenv("HELP_FILE", None)
if HELP_FILE:
    HELP_RESPONSES = json.load(open(f"common/commands_responses/{HELP_FILE}", "r"))
    COMMAND_RESPONSE_MAPPING["/help"] = HELP_RESPONSES
    COMMAND_RESPONSE_MAPPING["help"] = HELP_RESPONSES

START_DIALOG_FILE = getenv("START_DIALOG_FILE", None)
if START_DIALOG_FILE:
    START_DIALOG_RESPONSES = json.load(open(f"common/commands_responses/{START_DIALOG_FILE}", "r"))
    COMMAND_RESPONSE_MAPPING["/start_dialog"] = START_DIALOG_RESPONSES

if COMMAND_RESPONSE_MAPPING:
    available_commands = [f".?({command}).?$" for command in list(COMMAND_RESPONSE_MAPPING.keys())]
    AVAILABLE_COMMANDS = re.compile("|".join(available_commands), flags=re.IGNORECASE)

LANGUAGE = getenv("LANGUAGE", "EN")


def add_hypothesis(hyps_with_attrs, new_hyp_with_attrs):
    if new_hyp_with_attrs:
        cand, conf, attr, human_attr, bot_attr = new_hyp_with_attrs
        cands, confs, attrs, human_attrs, bot_attrs = hyps_with_attrs
        cands.append(cand)
        confs.append(conf)
        attrs.append(attr)
        human_attrs.append(human_attr)
        bot_attrs.append(bot_attr)


class DummySkillConnector:
    async def send(self, payload: Dict, callback: Callable):
        try:
            st_time = time.time()
            dialog = deepcopy(payload["payload"]["dialogs"][0])
            last_human_utt = dialog["human_utterances"][-1]["text"]

            # only look for commands if we have responses to at least some of them
            if AVAILABLE_COMMANDS and COMMAND_RESPONSE_MAPPING:
                commands_in_utt = AVAILABLE_COMMANDS.match(last_human_utt)
                if commands_in_utt:
                    discovered_command_groups = commands_in_utt.groups()
                    discovered_command = next(command for command in discovered_command_groups if command)
                    response_to_command = choice(COMMAND_RESPONSE_MAPPING[discovered_command])
                    hyps_with_attrs = [
                        [response_to_command],
                        [1],
                        [{"type": "command"}],
                        [{}],
                        [{}],
                    ]
                    asyncio.create_task(callback(task_id=payload["task_id"], response=hyps_with_attrs))
                    return

            # append at least basic dummy response
            if dialog["human_utterances"][-1].get("attributes", {}).get("documents", []):
                # if docs attached, append special dummy response
                hyps_with_attrs = [[choice(DUMMY_DOCS_RESPONSES)], [0.5], [{"type": "dummy"}], [{}], [{}]]
            else:
                hyps_with_attrs = [[choice(DUMMY_DONTKNOW_RESPONSES)], [0.5], [{"type": "dummy"}], [{}], [{}]]

            total_time = time.time() - st_time
            logger.info(f"dummy_skill exec time: {total_time:.3f}s")
            asyncio.create_task(callback(task_id=payload["task_id"], response=hyps_with_attrs))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=e))
