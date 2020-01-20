import argparse
import asyncio
import uuid
from statistics import mean, median
from time import time

import aiohttp

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', type=str)
parser.add_argument('-pf', '--phrasesfile', help='name of the file with phrases for dialog', type=str, default="")
parser.add_argument('-of', '--outputfile', help='name of the output file', type=str, default='output.csv')
parser.add_argument('-mnu', '--minusers', type=int, default=1)
parser.add_argument('-mxu', '--maxusers', type=int, default=10)

args = parser.parse_args()

try:
    with open(args.phrasesfile, 'r') as file:
        payloads = [line.rstrip('\n') for line in file]
except Exception as e:
    raise e


async def perform_test_dialogue(session, url, uuid, payloads):
    times = []
    for i in payloads:
        request_body = {'user_id': uuid, 'payload': i}
        start_time = time()
        async with session.post(url, json=request_body) as resp:
            response = await resp.json()
            end_time = time()
            if response['user_id'] != uuid:
                print('INFO, request returned wrong uuid')

        times.append(end_time - start_time)

    return times


async def run_users(url, payload, mnu, mxu):
    payload_len = len(payload)
    async with aiohttp.ClientSession() as session:
        for i in range(mnu, mxu + 1):
            tasks = []
            for _ in range(0, i):
                user_id = uuid.uuid4().hex
                tasks.append(asyncio.ensure_future(perform_test_dialogue(session, url, user_id, payload)))
            test_start_time = time()
            responses = await asyncio.gather(*tasks)
            test_time = time() - test_start_time
            times = []
            for resp in responses:
                times.extend(resp)

            print(f'test No {i} finished: {max(times)} {min(times)} {mean(times)} {median(times)} '
                  f'total_time {test_time} msgs {i*payload_len} mean_rps {(i*payload_len)/test_time}')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run_users(args.url, payloads, args.minusers, args.maxusers))
    loop.run_until_complete(future)
