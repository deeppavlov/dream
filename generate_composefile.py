import yaml
import argparse
from copy import deepcopy
from itertools import chain

from core.transform_config import SKILLS, ANNOTATORS, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS, PORT


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', type=str, default='docker-compose.yml')
parser.add_argument('--no_agent', help="don't create container for agent", action="store_true")
parser.add_argument('--no_db', help="don't create container for database (use external one)", action="store_true")

AGENT_BASIC = {
    'agent': {'build': {'context': './', 'dockerfile': 'dockerfile_agent'},
              'container_name': 'agent',
              'volumes': ['.:/dp-agent'],
              'ports': ['28888:8888'],
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
        self.template['build']['args']['gpu'] = 'false'
        self.template['ports'].append("{}:{}".format(skill_config['port'], skill_config['port']))

        env_vars = skill_config.get('env')
        if env_vars:
            self.template['environment'] = []
            for env, val in env_vars.items():
                self.template['environment'].append('{}={}'.format(env, '""' if not str(val).strip() else val))

        if skill_config.get('gpu'):
            self.template['runtime'] = 'nvidia'
            self.template['build']['args']['gpu'] = 'true'

    @property
    def config(self):
        return {self.container_name: self.template}


class DatabaseConfig:
    def __init__(self, port, template=None):
        if template is None:
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
    def __init__(self, agent=None, no_agent=False, no_db=False):
        self.no_agent = no_agent
        self.no_db = no_db
        if not self.no_agent:
            self.agent = agent
        self.skills = []
        self.database = []

    def add_skill(self, skill):
        if skill.external is True:
            return
        self.skills.append(skill)

    def add_db(self, db=None):
        if not self.no_db:
            self.database.append(db)

    def add_dependencies_to_agent(self):
        if not self.no_agent:
            for container in chain(self.skills, self.database):
                self.agent.add_dependence(container.container_name)

    @property
    def config(self):
        config_dict = {'version': '3', 'services': {}}
        self.add_dependencies_to_agent()
        for container in chain(self.skills, self.database):
            config_dict['services'].update(container.config)
        if not self.no_agent:
            config_dict['services'].update(self.agent.config)

        return dict(config_dict)


if __name__ == '__main__':
    args = parser.parse_args()

    dcc = DockerComposeConfig(AgentConfig(), args.no_agent, args.no_db)

    for conf in chain(SKILLS, ANNOTATORS, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS):
        dcc.add_skill(SkillConfig(conf))

    dcc.add_db(DatabaseConfig(PORT))

    with open(args.filename, 'w') as f:
        yaml.dump(dcc.config, f)
