Authentication
===============

Inherit from the abstract base class

    programy.security.authenticate.Authenticator

    class Authenticator(object):

        def __init__(self, configuration: BrainSecurityConfiguration):
            self._configuration = configuration

        @property
        def configuration(self):
            return self._configuration

        def get_default_denied_srai(self):
            return self.configuration.denied_srai

        def authenticate(self, clientid: str):
            return False