import argparse
import bz2
import json
import multiprocessing as mp
from logging import getLogger


parser = argparse.ArgumentParser()
parser.add_argument("-f", action="store", dest="dump_fname")
parser.add_argument("-d", action="store", dest="parsing_dir")
args = parser.parse_args()

logger = getLogger(__name__)

bz_file = bz2.BZ2File(args.dump_fname)
line = bz_file.readline()

manager = mp.Manager()
wiki_dict = manager.dict()

num_processors = 50


def process_sample(entity_dict):
    entity_id = ""
    triplets = []
    if "id" in entity_dict:
        entity_id = entity_dict["id"]
        try:
            if "labels" in entity_dict:
                if "ru" in entity_dict["labels"]:
                    name = entity_dict["labels"]["ru"]["value"]
                    triplets.append(["name_ru", name])
                if "en" in entity_dict["labels"]:
                    name = entity_dict["labels"]["en"]["value"]
                    triplets.append(["name_en", name])
        except Exception as e:
            logger.info(f"parsing error: {e}")

        try:
            if "aliases" in entity_dict:
                if "ru" in entity_dict["aliases"]:
                    aliases = [alias["value"] for alias in entity_dict["aliases"]["ru"]]
                    triplets.append(["aliases_ru"] + aliases)
                if "en" in entity_dict["aliases"]:
                    aliases = [alias["value"] for alias in entity_dict["aliases"]["en"]]
                    triplets.append(["aliases_en"] + aliases)
        except Exception as e:
            logger.info(f"parsing error: {e}")

        try:
            if "descriptions" in entity_dict:
                if "ru" in entity_dict["descriptions"]:
                    descr = entity_dict["descriptions"]["ru"]["value"]
                    triplets.append(["descr_ru", descr])
                if "en" in entity_dict["descriptions"]:
                    descr = entity_dict["descriptions"]["en"]["value"]
                    triplets.append(["descr_en", descr])
        except Exception as e:
            logger.info(f"parsing error: {e}")

        try:
            if (
                "sitelinks" in entity_dict
                and "ruwiki" in entity_dict["sitelinks"]
                and "title" in entity_dict["sitelinks"]["ruwiki"]
            ):
                wikipedia_title = entity_dict["sitelinks"]["ruwiki"]["title"]
                triplets.append(["ruwiki_page", wikipedia_title])
            if (
                "sitelinks" in entity_dict
                and "enwiki" in entity_dict["sitelinks"]
                and "title" in entity_dict["sitelinks"]["enwiki"]
            ):
                wikipedia_title = entity_dict["sitelinks"]["enwiki"]["title"]
                triplets.append(["enwiki_page", wikipedia_title])
        except Exception as e:
            logger.info(f"parsing error: {e}")

        if "claims" in entity_dict:
            for relation in entity_dict["claims"]:
                objects_list = []
                try:
                    objects = entity_dict["claims"][relation]
                    for obj in objects:
                        complex_obj = []
                        if "mainsnak" in obj and "datavalue" in obj["mainsnak"]:
                            if isinstance(obj["mainsnak"]["datavalue"]["value"], dict):
                                if "id" in obj["mainsnak"]["datavalue"]["value"]:
                                    complex_obj.append(obj["mainsnak"]["datavalue"]["value"]["id"])
                                if "amount" in obj["mainsnak"]["datavalue"]["value"]:
                                    complex_obj.append(obj["mainsnak"]["datavalue"]["value"]["amount"])
                                if "time" in obj["mainsnak"]["datavalue"]["value"]:
                                    complex_obj.append(
                                        obj["mainsnak"]["datavalue"]["value"]["time"].replace("T00:00:00Z", "")
                                    )
                                if "qualifiers" in obj:
                                    for key in obj["qualifiers"]:
                                        qua_list = obj["qualifiers"][key]
                                        complex_obj.append(key)
                                        for qua in qua_list:
                                            if (
                                                "datavalue" in qua
                                                and "value" in qua["datavalue"]
                                                and isinstance(qua["datavalue"]["value"], dict)
                                            ):
                                                if "id" in qua["datavalue"]["value"]:
                                                    complex_obj.append(qua["datavalue"]["value"]["id"])
                                                if "amount" in qua["datavalue"]["value"]:
                                                    complex_obj.append(qua["datavalue"]["value"]["amount"])
                                                if "time" in qua["datavalue"]["value"]:
                                                    complex_obj.append(
                                                        qua["datavalue"]["value"]["time"].replace("T00:00:00Z", "")
                                                    )
                                            if (
                                                "datavalue" in qua
                                                and "value" in qua["datavalue"]
                                                and isinstance(qua["datavalue"]["value"], str)
                                            ):
                                                if qua["datavalue"].get("type", "") == "string":
                                                    complex_obj.append(qua["datavalue"]["value"])
                            elif isinstance(obj["mainsnak"]["datavalue"]["value"], str) and relation in {
                                "P18",
                                "P154",
                                "P1545",
                            }:
                                complex_obj.append(obj["mainsnak"]["datavalue"]["value"])
                        if complex_obj:
                            objects_list.append(complex_obj)
                except Exception as e:
                    logger.info(f"error parsing triplets: {e}")
                if objects_list:
                    triplets.append([relation] + objects_list)

    return entity_id, triplets


def run(num_proc, num_chunk, common_list):
    wiki_dict = {}
    length = len(common_list)
    chunk_size = length // num_processors + 1
    for i in range(chunk_size):
        num_sample = num_processors * i + num_proc
        if num_sample < length:
            line = common_list[num_sample]
            line = line[:-2]
            try:
                entity = json.loads(line)
            except Exception as e:
                logger.info(f"json error: {e}")

            entity_id, triplets = process_sample(entity)
            if entity_id:
                if triplets:
                    wiki_dict[entity_id] = triplets

    with open(f"{args.parsing_dir}/{num_proc}_{num_chunk}.json", "w") as out:
        json.dump(wiki_dict, out)


num_chunk = 0
while True:
    logger.debug(f"num_chunk: {num_chunk}")
    common_list = []

    count = 0
    while line:
        line = bz_file.readline()
        common_list.append(line)
        count += 1
        if count == 10000 * num_processors:
            break
        if count % 50000 == 0:
            logger.debug(f"count: {count}")

    if not common_list:
        break

    workers = []
    for ii in range(num_processors):
        worker = mp.Process(target=run, args=(ii, num_chunk, common_list))
        workers.append(worker)
        worker.start()
    for worker in workers:
        worker.join()

    num_chunk += 1
