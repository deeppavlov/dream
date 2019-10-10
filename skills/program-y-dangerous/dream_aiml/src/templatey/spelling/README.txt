Spelling
=========

Inherit from the abstract base class

    programy.spelling.base.SpellingChecker


A single method 'correct' is passed the text to apply spelling correction to.
The text returned is the corrected text

    class SpellingChecker(object):
        __metaclass__ = ABCMeta

        def __init__(self, spelling_config=None):
            self.spelling_config = spelling_config

        @abstractmethod
        def correct(self, phrase):
            raise NotImplemented()

