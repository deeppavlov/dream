import argparse
from collections import defaultdict
from pathlib import Path

import requests
import yaml
from deeppavlov.core.data.utils import path_set_md5
from deeppavlov.download import get_configs_downloads
from git import Repo

parser = argparse.ArgumentParser()
parser.add_argument("--compose_file", help="path to compose file to analyze", default="docker-compose.yml")
parser.add_argument("-v", help="print url and model name", action="store_true")
args = parser.parse_args()

with open(args.compose_file) as f:
    data = yaml.load(f)

downloads = defaultdict(list)

repo = Repo("/pavlov/DeepPavlov")
origin = repo.remotes.origin

replace_paths = {
    "entity-detection": ('"src/', '"annotators/entity_detection/src/'),
    "kbqa": ('"/src/', '"annotators/kbqa/'),
}

for service_name, service_args in data["services"].items():
    if service_args.get("build", {}).get("args", {}).get("SRC_DIR") is not None:
        commit = service_args["build"]["args"].get("COMMIT", "master")
        repo.git.checkout(commit)
        config_path = Path(service_args["build"]["args"]["SRC_DIR"]) / service_args["build"]["args"]["CONFIG"]
        try:
            if service_name in {"entity-detection", "kbqa"}:
                with open(config_path) as fin:
                    lines = fin.readlines()
                with open(config_path, "w") as fout:
                    old_path, new_path = replace_paths[service_name]
                    fout.writelines([line.replace(old_path, new_path) for line in lines])
            config_downloads = dict(get_configs_downloads(config_path))
            for url, paths in config_downloads.items():
                md5_url = path_set_md5(url)
                resp = requests.get(md5_url)
                assert resp.status_code == 200, md5_url
                for line in resp.text.splitlines():
                    _md5, f_name = line.split(" ", maxsplit=1)
                    if f_name.startswith("*"):
                        f_name = f_name[1:]
                    else:
                        raise ValueError
                    for save_dir in paths:
                        downloads[str(save_dir / f_name)].append((service_name, url))
        except Exception as e:
            print(service_name)
            raise e

duplicates = {}
for key, val in downloads.items():
    urls = set([file_url for service_name, file_url in val])
    if len(urls) != 1:
        duplicates[key] = val

assert not duplicates, duplicates
