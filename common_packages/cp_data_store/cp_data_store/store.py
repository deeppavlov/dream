import json
import os
import pathlib

SERVICE_NAME = os.getenv("SERVICE_NAME")
SERVICE_DATA_DIR = "/data/services"

base_dir = pathlib.Path(SERVICE_DATA_DIR)

assert base_dir.is_dir(), f"Not found {SERVICE_DATA_DIR} dir"


def save2json_line(data, file_name, service_name=SERVICE_NAME):
    (base_dir / service_name).mkdir(exist_ok=True)
    (base_dir / service_name).chmod(0o777)
    save_file = base_dir / service_name / file_name
    with save_file.open("at") as in_f:
        in_f.write(json.dumps(data, ensure_ascii=False))
        in_f.write("\n")


def rm_file(file_name, service_name=SERVICE_NAME):
    (base_dir / service_name).mkdir(exist_ok=True)
    (base_dir / service_name).chmod(0o777)
    save_file = base_dir / service_name / file_name
    if save_file.is_file():
        save_file.unlink()
