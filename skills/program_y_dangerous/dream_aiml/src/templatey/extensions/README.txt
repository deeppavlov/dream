Extensions
===========

Inherit from the abstract base class

    programy.extensions.Extension

This class provides a single method to implement, execute, which takes bot, clientid and data as parameters. The data
parameter is a space seperated set of data that comes directly from the grammar calling the extension

    class Extension(object):
        __metaclass__ = ABCMeta

        @abstractmethod
        def execute(self, bot, clientid, data):
            raise NotImplemented()

