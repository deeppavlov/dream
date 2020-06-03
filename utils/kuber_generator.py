import yaml
import re
from pathlib import Path


def foo():
    with open(Path(__file__).resolve().parents[1] / 'docker-compose.yml') as f:
        x = yaml.load(f)
        return x['services']


def ports():
    with open(Path(__file__).resolve().parents[1] / 'dev.yml') as f:
        x = yaml.load(f)['services']
    resp = {}
    for name, body in x.items():
        if len(body['ports']) > 1:
            raise ValueError(f'len > 1 for {name}')
        a, b = body['ports'][0].split(':')
        if (a != b):
             raise ValueError(name)
        resp[name] = int(a)
    return resp

if __name__ == '__main__':
    resp = {}
    services = foo()
    ports = ports()

    gpu = 0
    for s_name, body in services.items():
        if s_name == 'agent':
            continue

        script = body.get('command')
        if script is None:
            if body['build']['dockerfile'] != 'dp/dockerfile_skill_gpu':
                raise ValueError(f"{body['build']['dockerfile']} in {s_name}")
            script = f'python -m deeppavlov riseapi {body["build"]["args"]["skillconfig"]} -p {body["build"]["args"]["skillport"]}'
        resp[f'socialbot_{s_name}'] = {
            'TEMPLATE': 'socialbot_service',
            'BASE_IMAGE': f'dp-agent-alexa_{s_name}',
            'CMD_SCRIPT': script,
            'CLUSTER_PORT': ports[s_name],
            'PORT': ports[s_name]
        }

        for constr in body.get('deploy', {}).get('placement', {}).get('constraints', []):
            if 'node.labels.with_gpu == true' in constr:
                resp[f'socialbot_{s_name}'].update({'GPU_UNITS_NUM': 1})
                gpu += 1
    print(f'total gpu containers {gpu}')

    with open('kuber.yml', 'w') as f:
        yaml.dump(resp, f, default_flow_style=False)
