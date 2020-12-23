import aiohttp
import asyncio
import argparse
import csv
import json
from time import time
from random import randrange
from signal import signal, SIGPIPE, SIG_DFL
import uuid
import logging

signal(SIGPIPE, SIG_DFL)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

'''
structure of dialog file (-df) should be written in json
{
    <uuid1>: [<phrase1.1>, <phrase1.2>, ...],
    <uuid2>: [<phrase2.1>, <phrase2.2>, ...],
    <uuid3>: [<phrase3.1>, <phrase3.2>, ...],
    ...
}
structure of phrase file (-pf) simple text file. One phrase per line
'''

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', type=str)
parser.add_argument('-uc', '--usercount', help='count of test users, which will send the message',
                    type=int, default=10)
parser.add_argument('-pc', '--phrasecount', help='count of phrases in single dialog',
                    type=int, default=10)
parser.add_argument('-pf', '--phrasesfile', help='name of the file with phrases for dialog', type=str, default="")
parser.add_argument('-df', '--dialogfile', help='name of the file with predefined dialogs', type=str, default="")
parser.add_argument('-cf', '--csvfile', help='name of the file with predefined dialogs in csv', type=str, default="")
parser.add_argument('-of', '--outputfile', help='name of the output file', type=str, default='output.csv')


async def perform_test_dialogue(session, url, uuid, payloads, with_debug_info=False):
    result = []
    for i in payloads:
        request_body = {'user_id': uuid, 'payload': i}
        start_time = time()
        try:
            async with session.post(url, json=request_body) as resp:
                resp.raise_for_status()
                response = await resp.json()
                end_time = time()
                # logger.debug("Time: {}; Request: {}; Response: {}".format(
                #     start_time - end_time, request_body, response)
                # )
                if request_body["payload"] in ["/start", "/close"]:
                    active_skill = 'command_performed'
                    response = {}
                    response['response'] = 'command_performed'
                    result.append([uuid, active_skill, start_time, end_time,
                                   end_time - start_time, len(i), i, response['response']])
                else:
                    if response['user_id'] != uuid:
                        logger.info('request returned wrong uuid')
                    active_skill = response['active_skill']
                    result.append([uuid, active_skill, start_time, end_time,
                                   end_time - start_time, len(i), i, response['response']])
                    if with_debug_info:
                        result[-1].append(response)
        except aiohttp.client_exceptions.ClientResponseError as e:
            logger.exception(e)
            end_time = time()
            active_skill = 'exception'
            result.append([uuid, active_skill, start_time, end_time, end_time - start_time, len(i), i, e])
            if with_debug_info:
                result[-1].append(e)

    return result


async def run(url, payloads, out_filename):
    tasks = []
    responses = []
    batch_size = 32
    async with aiohttp.ClientSession() as session:
        for i, k_v in enumerate(payloads.items()):
            k, v = k_v
            task = asyncio.ensure_future(perform_test_dialogue(session, url, k, v))
            tasks.append(task)
            if i % batch_size == 0:
                responses += await asyncio.gather(*tasks)
                tasks = []
    result = [['uuid', 'active_skill', 'send timestamp', 'receive timestamp', 'processing_time',
               'phrase length', 'phrase text', 'response']]
    for i in responses:
        result.extend(i)
    with open(out_filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=' ')
        for row in result:
            writer.writerow(row)


if __name__ == '__main__':
    args = parser.parse_args()
    payloads = {}

    if args.dialogfile:
        with open(args.dialogfile, 'r') as file:
            payloads = json.load(file)
    elif args.phrasesfile:
        with open(args.phrasesfile, 'r') as file:
            phrases = [line.rstrip('\n') for line in file]
        payloads = {uuid.uuid4().hex: [phrases[randrange(len(phrases))] for j in range(args.phrasecount)] for i in
                    range(args.usercount)}
    elif args.csvfile:
        with open(args.csvfile, 'r') as f:
            reader = csv.reader(f, delimiter=' ')
            phrases = [row[1] for row in reader][1:]
        payloads = {uuid.uuid4().hex: phrases}
    else:
        raise ValueError('You should provide either predefined dialog (-df) or file with phrases (-pf)')

    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    future = asyncio.ensure_future(run(args.url, payloads, args.outputfile))
    loop.run_until_complete(future)
