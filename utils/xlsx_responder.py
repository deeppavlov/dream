import pandas as pd
import argparse
import uuid
import asyncio
import aiohttp

from http_api_test import perform_test_dialogue

parser = argparse.ArgumentParser()
parser.add_argument('-input', '--input', help='input xlsx file')
parser.add_argument('-output', '--output', help='output xlsx file')
parser.add_argument('-url', '--url', help='url', default='http://0.0.0.0:4242')


async def main(args):
    writer = pd.ExcelWriter(args.output)
    dfs = pd.read_excel(args.input, sheet_name=None, header=None, names=['Sentence', 'Correct_answer'])
    for sheet_name, df in dfs.items():
        results = []
        async_size = 50
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(df['Sentence']), async_size):
                tasks = []
                for sent in df['Sentence'].values[i: i + async_size]:
                    uid = uuid.uuid4().hex
                    # result.append(await perform_test_dialogue(session, args.url, uid, ["/start", sent]))
                    task = asyncio.ensure_future(
                        perform_test_dialogue(session, args.url, uid, ['/start', sent])
                    )
                    tasks.append(task)
                result = await asyncio.gather(*tasks)
                results += result
            responses = []
            for r in results:
                assert len(r) == 2  # /start and sent
                responses.append(r[-1][-1])  # Collect only responses for sentences
            df['Response'] = responses
            df.to_excel(writer, sheet_name, index=False, header=True)
    writer.save()


if __name__ == '__main__':
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    future = asyncio.ensure_future(main(args))
    loop.run_until_complete(future)
