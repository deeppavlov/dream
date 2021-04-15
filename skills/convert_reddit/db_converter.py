# %%

import tqdm
import pickle
import pathlib
import json
import difflib
import logging
import aiohttp
import asyncio
import re
import copy


logger = logging.getLogger(__name__)


# %%
data_dir = pathlib.Path("data")
work_dir = pathlib.Path("tmp")

banned_responses_file = data_dir / "banned_responses_v2.json"
db_file = work_dir / "replies_v2.pkl"
output_db_file = work_dir / "replies_v3.pkl"

chache_file = work_dir / "chache.json"
dropped_responses_file = work_dir / "dropped_responses.json"
log_file = work_dir / "logs.txt"

response_encodings, responses = pickle.load(db_file.open("rb"))
# %%

marked_responses = [{"text": res, "index": i} for i, res in enumerate(responses)]


# %%
format_1 = re.compile(r"\s+(,|\.|!|\?)")
format_2 = re.compile(r"\s+(’)\s+")


def format_text(text):
    text = re.sub(format_1, r"\1", text)
    text = re.sub(format_2, r"'", text)
    return text


other_symbols_compiled = re.compile(r"[^a-zA-Z0-9\- ]", re.IGNORECASE)
space_compiled = re.compile(r"\s+", re.IGNORECASE)


def cleanup(text):
    cleaned = re.sub(other_symbols_compiled, "", text)
    cleaned = re.sub(space_compiled, " ", cleaned)
    return cleaned.strip()


def get_data_iter(data, split_n):
    ranges = range(0, len(data) + split_n, split_n)
    for begin_i, end_i in zip(ranges, ranges[1:]):
        yield data[begin_i:end_i]


def is_same(ground_truth, hypothesis, ratio=0.9):
    res_ratio = difflib.SequenceMatcher(None, ground_truth.split(), hypothesis.split()).ratio()
    return res_ratio >= ratio


async def aio_request(session, url, samples):
    try:
        new_samples = []
        async with session.post(url, json={"sentences": [subsample["text"] for subsample in samples]}) as resp:
            batch = await resp.json()
            assert len(batch) == len(samples)
            for b_el, subsample in zip(batch, samples):
                punct_text = b_el["punct_sent"]
                if bool(punct_text) and is_same(cleanup(b_el["punct_sent"]), cleanup(subsample["text"]), 0.95):
                    subsample["punct_text"] = punct_text
                else:
                    subsample["hyp_text"] = punct_text
                new_samples += [subsample]
        return new_samples
    except Exception as exc:
        raise exc
        return samples
    return samples


async def worker(url, data, batch_n):
    new_samples = []
    async with aiohttp.ClientSession() as session:
        while data["samples"]:
            batch = [data["samples"].pop() for _ in range(batch_n) if data["samples"]]
            new_samples += await aio_request(session, url, batch)
    return new_samples


async def load_bar(data):
    with tqdm.tqdm(total=len(data["samples"])) as pbar:
        cur_len = len(data["samples"])
        while data["samples"]:
            if cur_len != len(data["samples"]):
                pbar.update(cur_len - len(data["samples"]))
                cur_len = len(data["samples"])
            await asyncio.sleep(1)


async def load_data(samples, batch_n=10, worker_n=10):
    url = "http://a737ad642c7cc4356a543c2c58779eb6-1162604519.us-west-2.elb.amazonaws.com/sentseg/sentseg"
    data = {}
    data["samples"] = samples
    new_samples = []
    tasks = [asyncio.ensure_future(load_bar(data))]
    tasks += [asyncio.ensure_future(worker(url, data, batch_n)) for _ in range(worker_n)]
    new_samples = await asyncio.gather(*tasks)
    new_samples = [sample for sample in new_samples if sample]
    new_samples = sum(new_samples, [])
    return new_samples


# %%

loop = asyncio.get_event_loop()


unhandled_responses = copy.deepcopy(marked_responses)
handled_responses = [resp for resp in unhandled_responses if "punct_text" in resp]
i = 0
while unhandled_responses:
    i += 1
    if i > 5:
        break
    wip_responses = loop.run_until_complete(load_data(unhandled_responses, batch_n=10, worker_n=10))
    unhandled_responses = [resp for resp in wip_responses if "punct_text" not in resp]
    handled_responses += [resp for resp in wip_responses if "punct_text" in resp]
handled_responses = handled_responses + unhandled_responses
json.dump(handled_responses, open("cache_v2.json", "wt"), ensure_ascii=False, indent=4)
# %%

handled_responses = json.load(open("cache_v2.json", "rt"))

# %%
handled_responses = {
    resp["index"]: format_text(resp.get("punct_text", resp.get("hyp_text", resp["text"]))) for resp in handled_responses
}
max_index = max(list(handled_responses.keys()))
handled_responses = [handled_responses[i] for i in range(max_index + 1)]

pickle.dump([response_encodings, handled_responses], output_db_file.open("wb"))

# %%
print("old:")
print(responses[:20])
print("new:")
print(handled_responses[:20])
# %%
loop.close()
