Services
=========

Inherit from the abstract base class

    programy.services.service.Service

    class Service(object):
        __metaclass__ = ABCMeta

        def __init__(self, config: BrainServiceConfiguration):
            self._config = config

        @property
        def configuration(self):
            return self._config

        def load_additional_config(self, service_config):
            pass

        @abstractmethod
        def ask_question(self, bot, clientid: str, question: str):
            """
            Never knowingly Implemented
            """

