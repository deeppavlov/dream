import yaml
import argparse
from copy import deepcopy
from itertools import chain

from core.config import SKILLS, ANNOTATORS, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS
from core.connection import HOST, PORT

AGENT_BASIC = {
    'agent': {'build': {'context': './', 'dockerfile': 'dockerfile_agent'},
              'container_name': 'agent',
              'volumes': ['.:/dp-agent'],
              'ports': ['8888:8888'],
              'tty': True,
              'depends_on': []}
}

MONGO_BASIC = {
    'mongo': {'command': 'mongod',
              'image': 'mongo:3.2.0',
              'ports': ["'{}:27017'"],  # map port to none standard port, to avoid conflicts with locally installed mongodb.
              'volumes': ['/var/run/docker.sock:/var/run/docker.sock']}
}

SKILL_BASIC = {
    'build': {'context': './',
              'dockerfile': 'dockerfile_skill_basic',
              'args': {}},
    'volumes': ['.:/dp-agent',
                '${EXTERNAL_FOLDER}dp_logs:/logs',
                '${EXTERNAL_FOLDER}.deeppavlov:/root/.deeppavlov'],
    'ports': [],
    'tty': True,
}


class AgentConfig:
    def __init__(self, template=AGENT_BASIC):
        self.config = deepcopy(template)

    def add_dependence(self, container_name):
        self.config['agent']['depends_on'].append(container_name)

    def return_config_dict(self):
        return self.config


class SkillConfig:
    def __init__(self, skillconfig, template=SKILL_BASIC):
        self.template = deepcopy(template)
        self.external = skillconfig.get('external', False)
        self.parse_config(skillconfig)

    def parse_config(self, skillconfig):
        self.container_name = skillconfig['name']
        self.template['container_name'] = self.container_name
        self.template['build']['args']['skillport'] = skillconfig['port']
        self.template['build']['args']['skillconfig'] = skillconfig['path']
        self.template['ports'].append("{}:{}".format(skillconfig['port'], skillconfig['port']))

    def return_config_dict(self):
        return {self.container_name: self.template}


class DatabaseConfig:
    def __init__(self, host, port, template=MONGO_BASIC):
        self.template = {}
        self.container_name = ''
        if host == 'mongo':
            self.template = deepcopy(template)
            self.template['mongo']['ports'][0] == self.template['mongo']['ports'][0].format(port)
            self.container_name = 'mongo'

    def return_config_dict(self):
        return self.template


class DockerComposeConfig:
    def __init__(self, agent):
        self.agent = agent
        self.skills = []

    def add_skill(self, skill):
        if skill.external is True:
            return
        self.skills.append(skill)
        self.agent.add_dependence(skill.container_name)

    def add_db(self, db):
        if not db.container_name:
            return
        self.database = db
        self.agent.add_dependence(db.container_name)

    def return_config_dict(self):
        config_dict = {'version': '2.0', 'services': {}}
        for container in chain([self.agent], self.skills):
            config_dict['services'].update(container.return_config_dict())

        return dict(config_dict)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', type=str, default='docker-compose.yml')
    args = parser.parse_args()

    f = open(args.filename, 'w')

    dcc = DockerComposeConfig(AgentConfig())

    for conf in chain(SKILLS, ANNOTATORS, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS):
        dcc.add_skill(SkillConfig(conf))

    dcc.add_db(DatabaseConfig(HOST, PORT))

    f.write(yaml.dump(dcc.return_config_dict()))

    f.close()
