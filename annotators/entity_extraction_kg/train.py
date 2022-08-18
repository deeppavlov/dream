import argparse
import datetime
import os
import shutil
from copy import deepcopy
from logging import getLogger
from pathlib import Path

import pandas as pd
import torch
from filelock import FileLock

from deeppavlov import train_model, evaluate_model
from deeppavlov.core.commands.utils import parse_config

DATA_PATH = Path('/root/.deeppavlov/downloads')
LOCKFILE = DATA_PATH / 'lockfile'
LOG_PATH = DATA_PATH / 'logs'
LOG_PATH.mkdir(parents=True, exist_ok=True)
metrics_filename = DATA_PATH / "metrics_score_history.csv"
ner_config = parse_config("src/wiki_entity_detection.json")
logger = getLogger(__file__)


def evaluate(ner_config, after_training):
    res = evaluate_model(ner_config)
    logger.warning(f"metrics {res}")

    metrics = dict(res["test"])
    cur_f1 = metrics["ner_f1"]
    best_score = False

    if Path(metrics_filename).exists():
        df = pd.read_csv(metrics_filename)
        max_metric = max(df["old_metric"].max(), df["new_metric"].max())
        df = df.append({"time": datetime.datetime.now(),
                        "old_metric": max_metric,
                        "new_metric": cur_f1,
                        "update_model": cur_f1 > max_metric}, ignore_index=True)
        if cur_f1 > max_metric:
            best_score = True
    else:
        df = pd.DataFrame.from_dict({"time": [datetime.datetime.now()],
                                     "old_metric": [cur_f1],
                                     "new_metric": [cur_f1],
                                     "update_model": [False]})
        best_score = True

    if after_training:
        df.to_csv(metrics_filename, index=False)
    torch.cuda.empty_cache()

    return cur_f1, best_score


def train(data_path: str = ''):
    config = deepcopy(ner_config)
    if data_path:
        config["dataset_reader"] = {
            "class_name": "sq_reader",
            "data_path": data_path
        }
    init_path = next(
        i for i in config['metadata']['download'] if 'entity_detection_tinyroberta_42_sep.tar.gz' in i['url']
    )['subdir']
    model_path = config["metadata"]["variables"]["MODEL_PATH"]
    new_model_path = Path(f'{model_path}_new')
    new_model_path_exp = new_model_path.expanduser().resolve()
    model_path = Path(model_path)
    init_path_exp = Path(init_path).expanduser().resolve()

    if new_model_path_exp.exists():
        shutil.rmtree(new_model_path_exp)
    shutil.copytree(init_path_exp, new_model_path_exp)

    ent_path = new_model_path_exp / "tag_ent.dict"
    if ent_path.exists():
        os.remove(ent_path)

    config["metadata"]["variables"]["MODEL_PATH"] = str(new_model_path_exp)
    for i in range(len(config["chainer"]["pipe"])):
        if "torch_transformers_sequence_tagger" in config["chainer"]["pipe"][i].get("class_name", ""):
            config['chainer']['pipe'][i]['ent_linear_path'] = config['chainer']['pipe'][i]['load_path'].replace(str(model_path),
                                                                                                          str(new_model_path_exp))
            config['chainer']['pipe'][i]['using_custom_types'] = True
            logger.warning(f"load path {config['chainer']['pipe'][i]['ent_linear_path']}")
    config['chainer']['pipe'][2]["update_tag_dict"] = False
    config['chainer']['pipe'][6]["top_n"] = 1
    train_model(config)
    logger.warning('Training finished. Starting evaluation...')
    cur_f1, best_score = evaluate(config, True)

    if best_score:
        logger.warning(f'Model score is increased after training. Replacing old model with the new one.')
        shutil.rmtree(model_path)
        logger.warning(f'{model_path} removed')
        new_model_path.rename(model_path)
        logger.warning(f'{new_model_path} with trained model renamed to {model_path}')

    logger.warning('Training finished.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=str, default='')
    args = parser.parse_args()
    with FileLock(str(LOCKFILE)):
        train(args.data)
    LOCKFILE.unlink()
