Dynamic Maps
=============

Inherit from the abstract base class

    programy.dynamics.maps.DynamicMap

    class DynamicMap(object):
        __metaclass__ = ABCMeta

        def __init__(self, config):
            self._config = config

        @property
        def config(self):
            return self._config

        @abstractmethod
        def map_value(self, bot, clientid, value):
            raise NotImplemented()

Dynamic Maps should implement the single method map_value which returns the dynamically mapped value of the value
passed on.
