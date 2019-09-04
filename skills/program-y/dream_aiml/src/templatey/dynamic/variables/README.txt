Dynamic Variables
=============

Inherit from the abstract base class

    programy.dynamics.variables.DynamicVariable

    class DynamicVariable(object):
        __metaclass__ = ABCMeta

        def __init__(self, config):
            self._config = config

        @property
        def config(self):
            return self._config

        @abstractmethod
        def get_value(self, bot, clientid, data):
            raise NotImplemented()

Dynamic Variable should implement the single method get_value which should return a dynamically generated value for
the name of the variable passed into it. Data contains additional parameters as a space seperated string