import re
import shutil
import os
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from typing import Dict, Union


REPO_PATH = Path(__file__).resolve().parents[1]
KUBER_PATH = REPO_PATH / "kubernetes"
TEMPLATES_PATH = KUBER_PATH / "templates"
MODELS_PATH = KUBER_PATH / "models"
DOCKER_REGISTRY = os.getenv("DOCKER_REGISTRY")
NAMESPACE = os.getenv("NAMESPACE", "alexa")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
VERSION = os.getenv("VERSION", "latest")

env = Environment(loader=FileSystemLoader(TEMPLATES_PATH), trim_blocks=True, lstrip_blocks=True)
lb_template = env.get_template("kuber-lb.yaml")
dp_template = env.get_template("kuber-dp.yaml")


def read_yaml(yaml_path: Union[str, Path]) -> Dict:
    with open(yaml_path) as fin:
        data = yaml.load(fin.read(), Loader=yaml.FullLoader)
    return data


def write_file(file_path: Path, data: str) -> None:
    with open(file_path, "w") as fout:
        fout.write(data)


def get_port(service_params: Dict) -> int:
    ports = service_params["ports"]
    assert len(ports) == 1, f"{ports}"
    ports = list(map(int, ports[0].split(":")))
    # assert ports[0] == ports[1], f'{ports}'
    return ports[1]


def generate_network():
    compose = read_yaml(REPO_PATH / "docker-compose.yml")
    network = {"services": {}}
    for service_name, _ in compose["services"].items():
        network["services"][service_name] = {"build": {"network": "host"}}

    write_file(REPO_PATH / "network.yml", yaml.dump(network))


def generate_deployments():
    if MODELS_PATH.exists():
        shutil.rmtree(MODELS_PATH)

    dev = read_yaml(REPO_PATH / "dev.yml")
    compose = read_yaml(REPO_PATH / "docker-compose.yml").get("services")
    deploy = read_yaml(KUBER_PATH / "configs/deploy.yaml") or {}
    print("total services (inc. mongo and agent):", len(compose))

    for service_name, service_params in dev["services"].items():
        if service_name == "mongo":
            continue
        dp_name = f"{service_name}-dp"

        gpu = deploy.get(service_name, {}).get("gpu", "false")
        cuda = deploy.get(service_name, {}).get("CUDA_VISIBLE_DEVICES", "")
        resources = compose.get(service_name, {}).get("deploy", {}).get("resources")

        values_dict = {
            "KUBER_DP_NAME": dp_name,
            "REPLICAS": compose.get(service_name, {}).get("deploy", {}).get("replicas", 1),
            "resources": resources,
            "KUBER_IMAGE_TAG": f"{DOCKER_REGISTRY}/{service_name}:{VERSION}",
            "PORT": get_port(service_params),
            "GPU": str(gpu),
            "CUDA_VISIBLE_DEVICES": repr(cuda),
            "KUBER_LB_NAME": service_name,
            "CLUSTER_IP": "10.100.198.105",  # REPLACE WITH CORRECT!!!!!!!!!
            "CLUSTER_PORT": get_port(service_params),  # REPLACE WITH CORRECT!!!!!!!!!
            "ENVIRONMENT": ENVIRONMENT,
            "NAMESPACE": NAMESPACE,
        }

        if "command" in compose.get(service_name, []):
            command = compose.get(service_name, {}).get("command", "")
            if command.startswith(
                ("gunicorn", "uvicorn", "cd /src/dream_aiml/scripts", "bash server_run.sh", "flask", "python")
            ):
                values_dict.update({"COMMAND": command})
            elif command.startswith("sh -c") or command.startswith("bash -c"):
                command = re.findall(r"(bash -c|sh -c) [\'\"](.+)[\'\"]$", command)[0][1]
                values_dict.update({"COMMAND": command})
            else:
                raise ValueError(service_name, command)

        if service_name == "agent":
            values_dict.update({"WAIT_HOSTS": compose["agent"]["environment"]["WAIT_HOSTS"], "WAIT_HOSTS_TIMEOUT": 480})

        envs = compose.get(service_name, {}).get("environment", [])
        if isinstance(envs, dict):
            envs = [env for env in envs.items()]
        elif isinstance(envs, list):
            envs = [env.split("=") for env in envs]
        else:
            envs = []
        envs = [
            {"name": env[0], "value": env[1]}
            for env in envs
            if env[0] not in ["CUDA_VISIBLE_DEVICES", "WAIT_HOSTS", "WAIT_HOSTS_TIMEOUT"]
        ]
        values_dict["ENVS"] = envs
        if "~/.deeppavlov:/root/.deeppavlov" in service_params.get("volumes", []):
            values_dict.update({"COMPONENTS_VOLUME": "True"})
        model_path = MODELS_PATH / service_name
        model_path.mkdir(parents=True)

        write_file(model_path / f"{dp_name}.yaml", dp_template.render(values_dict))
        write_file(model_path / f"{service_name}-lb.yaml", lb_template.render(values_dict))


if __name__ == "__main__":
    generate_network()
    generate_deployments()
