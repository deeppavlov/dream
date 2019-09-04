Dynamic Sets
=============

Inherit from the abstract base class

    programy.dynamics.sets.DynamicSet

    class DynamicSet(object):
        __metaclass__ = ABCMeta

        def __init__(self, config):
            self._config = config

        @property
        def config(self):
            return self._config

        @abstractmethod
        def is_member(self, bot, clientid, value):
            raise NotImplemented()

Dynamic Sets should implement the single method is_member which should return a boolean value representing whether
the passed value is a member of the set or not