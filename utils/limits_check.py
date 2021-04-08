#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
from pathlib import Path
import docker


absolute_path = Path(__file__).absolute().parents[1]
compose = absolute_path / "docker-compose.yml"


def check_limits(service):
    client = docker.APIClient(base_url="unix://var/run/docker.sock")
    with open(compose) as f:
        data = yaml.load(f.read(), Loader=yaml.FullLoader)

    service_dict = data.get("services").get(service)
    context = service_dict.get("build", {}).get("context", ".")
    command = service_dict.get("command")
    mem_limit = service_dict.get("deploy", {}).get("resources", {}).get("limits", {}).get("memory", "256M")

    print("Building image...")
    image = client.build(
        path=str(absolute_path / context),
        rm=True,
        tag=f"{service}:local",
        decode=True,
    )

    for chunk in image:
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                print(line)

    host_config = client.create_host_config(
        auto_remove=True,
        mem_limit=mem_limit,
    )

    try:
        stop = client.stop(
            container="dp",
        )

        print(f"stop={stop}")
    except docker.errors.NotFound:
        pass

    try:
        remove = client.remove(
            container="dp",
        )
        print(f"remove={remove}")
    except Exception:
        pass

    print("Starting image...")
    container = client.create_container(
        image=f"{service}:local",
        command=command,
        detach=True,
        stdin_open=True,
        tty=True,
        name="dp",
        host_config=host_config,
    )

    client.start(
        container=container.get("Id"),
    )

    logs = client.attach(
        container=container.get("Id"),
        stdout=True,
        stderr=True,
        timestamps=True,
    )

    try:
        while True:
            line = next(logs).decode("utf-8")
            print(line)
    except StopIteration:
        print(f"log stream ended for {service}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        service = sys.argv[1]
        sys.exit(check_limits(service))
    else:
        print(f"Usage: {os.path.basename(__file__)} service_name")
