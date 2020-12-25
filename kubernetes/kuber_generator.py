import json
import re
import shutil
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


from typing import Dict, Union
import yaml

REPO_PATH = Path(__file__).resolve().parents[1]
KUBER_PATH = REPO_PATH / 'kubernetes'
TEMPLATES_PATH = KUBER_PATH / 'templates'
MODELS_PATH = KUBER_PATH / 'models'
DOCKER_REGISTRY = os.getenv('DOCKER_REGISTRY')

env = Environment(loader=FileSystemLoader(TEMPLATES_PATH), trim_blocks=True, lstrip_blocks=True)
lb_template = env.get_template('kuber-lb.yaml')
dp_template = env.get_template('kuber-dp.yaml')


def read_yaml(yaml_path: Union[str, Path]) -> Dict:
    with open(yaml_path) as fin:
        data = yaml.load(fin.read(), Loader=yaml.FullLoader)
    return data


def write_file(file_path: Path, data: str) -> None:
    with open(file_path, 'w') as fout:
        fout.write(data)


def get_port(service_params: Dict) -> int:
    ports = service_params['ports']
    assert len(ports) == 1, f'{ports}'
    ports = list(map(int, ports[0].split(':')))
    assert ports[0] == ports[1], f'{ports}'
    return ports[0]

def generate_network():
    compose = read_yaml(REPO_PATH / 'docker-compose.yml')
    network = {'services': {}}
    for service_name, _ in compose['services'].items():
        network['services'][service_name] = {'build': {'network': 'host'}}

    write_file(REPO_PATH / 'network.yml', yaml.dump(network))

def generate_deployments():
    if MODELS_PATH.exists():
        shutil.rmtree(MODELS_PATH)

    dev = read_yaml(REPO_PATH / 'dev.yml')
    compose = read_yaml(REPO_PATH / 'docker-compose.yml')
    deploy = read_yaml(KUBER_PATH / 'configs/deploy.yaml') or {}
    print('total services (inc. mongo and agent):', len(dev['services']))

    for service_name, service_params in dev['services'].items():
        if service_name == 'mongo':
            continue
        dp_name = f'{service_name}-dp'

        cuda = deploy.get(service_name, {}).get('CUDA_VISIBLE_DEVICES', '')

        values_dict = {
            'KUBER_DP_NAME': dp_name,
            'REPLICAS_NUM': deploy.get(service_name, {}).get('REPLICAS_NUM', 1),
            'KUBER_IMAGE_TAG': f'{DOCKER_REGISTRY}/{service_name}',
            'PORT': get_port(service_params),
            'CUDA_VISIBLE_DEVICES': repr(cuda),
            'KUBER_LB_NAME': service_name,
            'CLUSTER_IP': '10.100.198.105',  # REPLACE WITH CORRECT!!!!!!!!!
            'CLUSTER_PORT': get_port(service_params),  # REPLACE WITH CORRECT!!!!!!!!!
            'ENVIRONMENT': 'A'
        }

        if 'command' in compose['services'].get(service_name, []):
            command = compose['services'][service_name]['command']
            if command.startswith(('gunicorn', 'uvicorn', 'cd /src/dream_aiml/scripts', 'bash server_run.sh')):
                values_dict.update({'COMMAND': command})
            elif command.startswith('sh -c') or command.startswith('bash -c'):
                command = re.findall(r'(bash -c|sh -c) [\'\"](.+)[\'\"]$', command)[0][1]
                values_dict.update({'COMMAND': command})
            else:
                raise ValueError(service_name, command)

        if service_name == 'agent':
            values_dict.update({
                'WAIT_HOSTS': compose['services']['agent']['environment']['WAIT_HOSTS'],
                'WAIT_HOSTS_TIMEOUT': 480
            })

        if "~/.deeppavlov:/root/.deeppavlov" in service_params.get('volumes', []):
            values_dict.update({'COMPONENTS_VOLUME': 'True'})
        model_path = MODELS_PATH / service_name
        model_path.mkdir(parents=True)

        write_file(model_path / f'{dp_name}.yaml', dp_template.render(values_dict))
        write_file(model_path / f'{service_name}-lb.yaml', lb_template.render(values_dict))


if __name__ == '__main__':
    generate_network()
    generate_deployments()
