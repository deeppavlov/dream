import yaml
import argparse

# USAGE: python ./utils/clean_ports_docker_compose.py --dc docker-compose.yml --staging staging.yml

parser = argparse.ArgumentParser()
parser.add_argument('--dc', help='path to docker-compose.yml', default='docker-compose.yml')
parser.add_argument('--staging', help='path to staging.yml', default='staging.yml')

if __name__ == '__main__':
    args = parser.parse_args()
    dc_yml_file = args.dc
    staging_yml_file = args.staging
    # remove ports from docker-compose.yml
    dc_yml = yaml.load(open(dc_yml_file, 'r'), Loader=yaml.FullLoader)
    if 'ports' in dc_yml['services']['agent']:
        del dc_yml['services']['agent']['ports']
    yaml.dump(dc_yml, open(dc_yml_file, 'w'))
    # add port to staging.yml
    staging_yml = yaml.load(open(staging_yml_file, 'r'), Loader=yaml.FullLoader)
    staging_yml['services']['agent']['ports'] = ['${DP_AGENT_PORT}:4242']
    yaml.dump(staging_yml, open(staging_yml_file, 'w'))
