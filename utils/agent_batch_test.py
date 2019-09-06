from datetime import datetime
import uuid
import argparse
import os
from random import choice

from core.agent import Agent
from core.state_manager import StateManager
from core.skill_manager import SkillManager
from core.rest_caller import RestCaller
from models.postprocessor import DefaultPostprocessor
from models.response_selector import ConfidenceResponseSelector
from core.transform_config import MAX_WORKERS, ANNOTATORS, SKILL_SELECTORS, SKILLS, RESPONSE_SELECTORS

import logging

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

os.environ["DPA_LAUNCHING_ENV"] = 'local'

parser = argparse.ArgumentParser()
parser.add_argument('phrasefile', help='name of the file with phrases for dialog', type=str,
                    default="../utils/ru_test_phrases.txt")


def init_agent():
    state_manager = StateManager()

    preprocessors = []
    for ants in ANNOTATORS:
        if ants:
            anno_names, anno_urls, anno_formatters = zip(
                *[(a['name'], a['url'], a['formatter']) for a in ants])
        else:
            anno_names, anno_urls, anno_formatters = [], [], []
        preprocessors.append(RestCaller(max_workers=MAX_WORKERS, names=anno_names, urls=anno_urls,
                                        formatters=anno_formatters))
    postprocessor = DefaultPostprocessor()
    skill_caller = RestCaller(max_workers=MAX_WORKERS)

    if RESPONSE_SELECTORS:
        rs_names, rs_urls, rs_formatters = zip(
            *[(rs['name'], rs['url'], rs['formatter']) for rs in RESPONSE_SELECTORS])
        response_selector = RestCaller(max_workers=MAX_WORKERS, names=rs_names, urls=rs_urls,
                                       formatters=rs_formatters)
    else:
        response_selector = ConfidenceResponseSelector()

    skill_selector = None
    if SKILL_SELECTORS:
        ss_names, ss_urls, ss_formatters = zip(
            *[(ss['name'], ss['url'], ss['formatter']) for ss in SKILL_SELECTORS])
        skill_selector = RestCaller(max_workers=MAX_WORKERS, names=ss_names, urls=ss_urls,
                                    formatters=ss_formatters)

    skill_manager = SkillManager(skill_selector=skill_selector, response_selector=response_selector,
                                 skill_caller=skill_caller,
                                 profile_handlers=[skill['name'] for skill in SKILLS
                                                   if skill.get('profile_handler')])

    agent = Agent(state_manager, preprocessors, postprocessor, skill_manager)
    return agent


def main():
    args = parser.parse_args()
    with open(args.phrasefile, 'r') as file:
        phrases = [line.rstrip('\n') for line in file]
        length = len(phrases)

    u_tg_ids = [str(uuid.uuid4())] * length
    u_d_types = [choice(['iphone', 'android']) for _ in range(length)]
    date_times = [datetime.utcnow()] * length
    locations = [choice(['moscow', 'novosibirsk', 'novokuznetsk']) for _ in range(length)]
    ch_types = ['cmd_client'] * length

    agent = init_agent()

    responses = agent(utterances=phrases, user_telegram_ids=u_tg_ids, user_device_types=u_d_types,
                      date_times=date_times, locations=locations, channel_types=ch_types)
    return responses


if __name__ == "__main__":
    print(main())
