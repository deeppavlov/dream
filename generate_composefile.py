import yaml
import argparse
from copy import deepcopy
from itertools import chain

from core.config import SKILLS, ANNOTATORS, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS, HOST, PORT


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', type=str, default='docker-compose.yml')

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
              'ports': ['{}:27017'],
              # map port to none standard port, to avoid conflicts with locally installed mongodb.
              'volumes': ['/var/run/docker.sock:/var/run/docker.sock']}
}

SKILL_BASIC = {
    'build': {'context': './',
              'dockerfile': 'dockerfile_skill_basic',
              'args': {}},
    'volumes': ['.:/dp-agent',
                '${EXTERNAL_FOLDER}/dp_logs:/logs',
                '${EXTERNAL_FOLDER}/.deeppavlov:/root/.deeppavlov'],
    'ports': [],
    'tty': True,
}


class Config:
    def __init__(self, template):
        self.template = template
        if template is not None:
            self._config = deepcopy(template)


class AgentConfig(Config):
    def __init__(self, template=None):
        if template is None:
            template = deepcopy(AGENT_BASIC)
        else:
            template = deepcopy(template)

        super().__init__(template)

    def add_dependence(self, container_name):
        self._config['agent']['depends_on'].append(container_name)

    @property
    def config(self):
        return self._config


class SkillConfig(Config):
    def __init__(self, skill_config, template=None):
        if template is None:
            template = deepcopy(SKILL_BASIC)
        else:
            template = deepcopy(template)

        super().__init__(template)

        self.external = skill_config.get('external', False)
        self.container_name = None
        self.parse_config(skill_config)

    def parse_config(self, skill_config):
        self.container_name = skill_config['name']
        self.template['container_name'] = self.container_name
        self.template['build']['args']['skillport'] = skill_config['port']
        self.template['build']['args']['skillconfig'] = skill_config['path']
        self.template['build']['args']['skill_endpoint'] = skill_config['endpoint']
        self.template['build']['args']['skillhost'] = '0.0.0.0'
        self.template['ports'].append("{}:{}".format(skill_config['port'], skill_config['port']))

    @property
    def config(self):
        return {self.container_name: self.template}


class DatabaseConfig:
    def __init__(self, host, port, template=None):
        if template is None and host == '127.0.0.1':
            self.template = deepcopy(MONGO_BASIC)
            self.container_name = 'mongo'
            self.template['mongo']['ports'][0] = self.template['mongo']['ports'][0].format(port)
        else:
            self.template = deepcopy(template)
            self.container_name = None

    @property
    def config(self):
        return self.template


class DockerComposeConfig:
    def __init__(self, agent):
        self.agent = agent
        self.skills = []
        self.database = []

    def add_skill(self, skill):
        if skill.external is True:
            return
        self.skills.append(skill)
        self.agent.add_dependence(skill.container_name)

    def add_db(self, db):
        if not db.container_name:
            return
        self.database.append(db)
        self.agent.add_dependence(db.container_name)

    @property
    def config(self):
        config_dict = {'version': '2.0', 'services': {}}
        for container in chain([self.agent], self.skills, self.database):
            config_dict['services'].update(container.config)

        return dict(config_dict)


if __name__ == '__main__':
    args = parser.parse_args()

    dcc = DockerComposeConfig(AgentConfig())

    for conf in chain(SKILLS, ANNOTATORS, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS):
        dcc.add_skill(SkillConfig(conf))

    dcc.add_db(DatabaseConfig(HOST, PORT))

    with open(args.filename, 'w') as f:
        yaml.dump(dcc.config, f)
