import logging
import time
from multiprocessing import Process

import click
import requests
from python_on_whales import DockerClient

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def healthcheck(docker: DockerClient, timeout: float) -> None:
    # TODO: add healthchecks to containers and look at this status.
    end_time = time.time() + timeout
    while True:
        time.sleep(5)
        containers = docker.compose.ps(all=True)

        exited_containers = [c for c in containers if c.state.status == "exited"]
        if exited_containers:
            logger.error(f"Following containers are exited: {', '.join([c.name for c in exited_containers])}.")
            for container in exited_containers:
                logger.error(f"{container.name} output:")
                logger.error(container.logs())
            raise RuntimeError("Found exited containers")

        not_running_containers = [c for c in containers if c.state.running is False]

        if not_running_containers:
            logger.info(f'Waiting {", ".join([c.name for c in not_running_containers])} to run.')
        else:
            logger.info("All containers are running.")
        try:
            resp = requests.get("http://0.0.0.0:4242/ping")
            if resp.status_code == 200 and not not_running_containers:
                return
        except requests.exceptions.ConnectionError:
            logger.info("Agent's ping is still unavailable")

        if time.time() > end_time:
            if not_running_containers:
                logger.error(f"Failed to run " f'{", ".join([c.name for c in not_running_containers])}.')
            raise TimeoutError("Failed to start.")


@click.command()
@click.option("--mode", type=click.Choice(["build", "up", "clean", "logs"]))
@click.option(
    "--compose-file",
    "-f",
    default=["docker-compose.yml"],
    help="Path to docker compose file.",
    multiple=True,
)
@click.option("--wait-timeout", default=480, help="How long to wait", type=float)
def main(mode, compose_file, wait_timeout):
    compose_file = list(compose_file)
    docker = DockerClient(compose_files=compose_file, compose_project_name="test")
    if mode == "build":
        process = Process(target=docker.compose.build)
        process.start()
        process.join()
        print(process.exitcode)
        if process.exitcode:
            raise SystemExit(f"Got {process.exitcode} exit code.")
    elif mode == "up":
        process = Process(target=docker.compose.up(detach=True))
        process.start()
        healthcheck(docker, wait_timeout)
    elif mode == "clean":
        docker.compose.kill()
        docker.compose.down(remove_orphans=True, volumes=True)
        docker.compose.rm(stop=True, volumes=True)
    elif mode == "logs":
        for c in docker.compose.ps(all=True):
            logger.info(f"{c.name} logs:")
            logger.info(c.logs())


if __name__ == "__main__":
    main()
