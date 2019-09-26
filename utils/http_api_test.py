import aiohttp
import asyncio
import argparse
import csv
import json
from time import time
from random import randrange
import uuid

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
parser.add_argument('-of', '--outputfile', help='name of the output file', type=str, default='output.csv')

args = parser.parse_args()
payloads = {}

if args.dialogfile:
    try:
        with open(args.dialogfile, 'r') as file:
            payloads = json.load(file)
    except Exception as e:
        raise e
elif args.phrasesfile:
    try:
        with open(args.phrasesfile, 'r') as file:
            phrases = [line.rstrip('\n') for line in file]
    except Exception as e:
        raise e
    payloads = {uuid.uuid4().hex: [phrases[randrange(len(phrases))] for j in range(args.phrasecount)] for i in
                range(args.usercount)}
else:
    raise ValueError('You should provide either predefined dialog (-df) or file with phrases (-pf)')


async def perform_test_dialogue(session, url, uuid, payloads):
    result = []
    for i in payloads:
        request_body = {'user_id': uuid, 'payload': i}
        start_time = time()
        async with session.post(url, json=request_body) as resp:
            response = await resp.json()
            end_time = time()
            if response['user_id'] != uuid:
                print('INFO, request returned wrong uuid')
            result.append([uuid, start_time, end_time, end_time - start_time, len(i), i])

    return result


async def run(url, payloads, out_filename):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for k, v in payloads.items():
            task = asyncio.ensure_future(perform_test_dialogue(session, url, k, v))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
    result = [['uuid', 'send timestamp', 'receive timestamp', 'processing_time', 'phrase length', 'phrase text']]
    for i in responses:
        result.extend(i)
    with open(out_filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=' ')
        for row in result:
            writer.writerow(row)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(args.url, payloads, args.outputfile))
    loop.run_until_complete(future)
