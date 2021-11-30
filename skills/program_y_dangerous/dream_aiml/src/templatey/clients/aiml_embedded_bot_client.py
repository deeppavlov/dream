import sys
import os
from programy.config.file.yaml_file import YamlConfigurationFile
from programy.config.programy import ProgramyConfiguration
from programy.clients.args import CommandLineClientArguments
from programy.clients.client import BotClient
from programy.utils.license.keys import LicenseKeys
from programy.utils.substitutions.substitues import Substitutions
from programy.clients.botfactory import BotFactory
from programy.clients.events.console.config import ConsoleConfiguration


class AIMLEmbeddedBotClient(BotClient):
    def __init__(self, id, config_file_path, src_root_path=None):
        """
        BotClient that can be initilized in runtime from YAML config

        WARNING this module changes CWD (Current Working Directory)!

        ProgramY has assumptions about current directories and uses environmental variables
        to specify search paths when launched from bash scripts.

        First, ProgramY uses file paths relative to config file.
        Second, ProgramY allows to specify paths to modules which are in dot notation relative to
            project root, which is different from config dir and usually placed 2 directories higher

        In this module we gather all this configurations via parameters.

        :param id: str, unique identifier of the bot
        :param config_file_path: path to the YAML config file
        :param src_root_path: sometimes YAML config path asserts that we reference to
            modules which are part of another project, and src_modules_root_path - is a path from
            which we look for specified modules. For example YAML config
                joiner:
                    classname: templatey.processors.sentence_joiner_deduplicator.SentenceJoinerDeDuplicator
            means that a class SentenceJoinerDeDuplicator will be searched from
            src_modules_root_path by appending dot prefixes.

        """
        self._id = id
        self._license_keys = LicenseKeys()
        self._storage = None
        self._scheduler = None
        self._email = None
        self._trigger_mgr = None
        self._configuration = None
        self._ping_responder = None

        self._questions = 0

        self._arguments = self.parse_arguments(argument_parser=None)

        # hack:
        if self._arguments._logging == 10:
            self._arguments._logging = None

        self.initiate_logging(self.arguments)

        self._subsitutions = Substitutions()
        if self.arguments.substitutions is not None:
            self._subsitutions.load_substitutions(self.arguments.substitutions)

        # specify configuration file
        self._config_filename = config_file_path

        self.load_configuration(self.arguments)
        # self.parse_configuration()

        self.load_storage()

        ##############################################################################
        # set path because config uses relative paths
        # this required so the files specified as relative paths in YAML will be interpreted
        # correctly like in the example:
        # categories_storage:
        #                   dirs: ../../storage/categories
        #                   subdirs: true
        #                   extension: .aiml
        current_dir_path = os.path.dirname(self._config_filename)
        os.chdir(current_dir_path)
        ##############################################################################

        ##############################################################################
        # to be able to find modules of dream aiml such as SentenceDeduplicator
        if not src_root_path:
            src_root_path = os.path.dirname(os.path.dirname(current_dir_path))
            src_root_path += "/src"
        sys.path.append(src_root_path)
        ##############################################################################

        self._bot_factory = BotFactory(self, self.configuration.client_configuration)

        self.load_license_keys()
        self.get_license_keys()
        self._configuration.client_configuration.check_for_license_keys(self._license_keys)

        self.load_scheduler()

        self.load_renderer()

        self.load_email()

        self.load_trigger_manager()

        self.load_ping_responder()

    def get_client_configuration(self):
        return ConsoleConfiguration()

    def parse_arguments(self, argument_parser):
        client_args = CommandLineClientArguments(self, parser=None)
        return client_args

    def load_configuration(self, arguments):

        client_config = self.get_client_configuration()
        self._configuration = ProgramyConfiguration(client_config)

        yaml_file = YamlConfigurationFile()
        yaml_file.load_from_file(self._config_filename, client_config, ".")

    def process_question(self, client_context, question):
        self._questions += 1
        return client_context.bot.ask_question(client_context, question, responselogger=self)

    def handle_user_message(self, user_id, message_text):
        """Interface method to retrieve response of particular bot for a message
        from particular user"""
        client_context = self.create_client_context(user_id)
        response = self.process_question(client_context, message_text)
        return response
