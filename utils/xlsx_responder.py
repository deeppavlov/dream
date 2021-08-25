import argparse
import uuid
import asyncio
import aiohttp
import pathlib
import json
import datetime
import logging
import collections
import traceback

import tqdm
import pandas as pd

from http_api_test import perform_test_dialogue


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="input xlsx file", type=pathlib.Path)
parser.add_argument("-o", "--output", help="output xlsx file", type=pathlib.Path)
timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
parser.add_argument(
    "-c", "--cache", help="json cache file", type=pathlib.Path, default=pathlib.Path(f"/tmp/cache_{timestamp}.json")
)
parser.add_argument("-l", "--url", help="url", default="http://0.0.0.0:4242")
parser.add_argument("-n", "--hypothesis_n", help="number of hypotheses", default=3, type=int)
parser.add_argument("-b", "--batch_size", help="batch size", default=5, type=int)


def parse_hypothesis(
    raw_hypothesis=[
        "dialog_id",
        "",
        0,
        0,
        -1,
        0,
        "",
        "",
    ]
):
    _, active_skill, _, _, exec_time, _, request, response = raw_hypothesis
    return {
        "active_skill": active_skill,
        "exec_time": exec_time,
        "request": request,
        "response": response,
    }


async def main(args):
    writer = pd.ExcelWriter(args.output)
    dfs = pd.read_excel(args.input, sheet_name=None, header=None, names=["Sentence", "Correct_answer"])
    if args.cache.exists():
        sent2data = json.load(args.cache.open("rt"))
    else:
        sent2data = {}
        for sheet_name, df in dfs.items():
            for sent in df["Sentence"].values:
                sent2data[sent] = {
                    "sheet_name": sheet_name,
                    "request": sent,
                    "hypotheses": [],
                }
    sents = [sent for sent, obj in sent2data.items() if not obj["hypotheses"]]
    async with aiohttp.ClientSession() as session:
        for i in tqdm.tqdm(
            range(0, len(sents), args.batch_size),
            total=len(sents) // args.batch_size + int(bool(len(sents) % args.batch_size)),
        ):
            tasks = []
            for sent in sents[i : i + args.batch_size]:
                uid = uuid.uuid4().hex
                task = asyncio.ensure_future(
                    perform_test_dialogue(session, args.url, uid, ["hi"] + ["bla", sent] * args.hypothesis_n)
                )
                tasks.append(task)
            try:
                results = await asyncio.gather(*tasks)
                assert len(tasks) == len(results)
                sent2hypotheses = {}
                for sent, result in zip(sents[i : i + args.batch_size], results):
                    none_bla_raw_hypotheses = result[-2 * args.hypothesis_n : :][::-2][::-1]
                    assert len(none_bla_raw_hypotheses) == args.hypothesis_n
                    hypotheses = [parse_hypothesis(raw_hyp) for raw_hyp in none_bla_raw_hypotheses]
                    sent2hypotheses[sent] = hypotheses
                [sent2data[sent]["hypotheses"].extend(hypotheses) for sent, hypotheses in sent2hypotheses.items()]
                json.dump(sent2data, args.cache.open("wt"), indent=4, ensure_ascii=False)
            except Exception:
                logger.error(traceback.format_exc())
    sheet_name2data = collections.defaultdict(list)
    for data in sent2data.values():
        sheet_name2data[data["sheet_name"]] += [data]
    for sheet_name, data in sheet_name2data.items():
        df = {}
        df["requests"] = [i["request"] for i in data]
        hypothesis_series = list(zip(*[i["hypotheses"] + [parse_hypothesis()] * args.hypothesis_n for i in data]))[
            : args.hypothesis_n
        ]
        for i, hypothesis in enumerate(hypothesis_series):
            df[f"active_skills_{i}"] = [hyp["active_skill"] for hyp in hypothesis]
            df[f"responses_{i}"] = [hyp["response"] for hyp in hypothesis]
        pd.DataFrame(df).to_excel(writer, sheet_name, index=False, header=True)
        writer.save()


if __name__ == "__main__":
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=False)
    future = asyncio.ensure_future(main(args))
    loop.run_until_complete(future)
