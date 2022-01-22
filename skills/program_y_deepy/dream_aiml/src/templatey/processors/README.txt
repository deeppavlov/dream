Processors
===========

There are 2 types of processors

    o Pre Processors. Which convert the raw text of the question entered into the bot before it is passed to the
                      brain to answer

    o Post Processors. Which convert the raw answer after it has been returned from the brain

Pre Processors inherit from the abstract base class

    programy.processors.processing.PreProcessor

The class has a single method, process, which takes bot, client and the string to pre-process and should return the processed string

    class PreProcessor(Processor):

        def __init__(self):
            Processor.__init__(self)

        @abstractmethod
        def process(self, bot, clientid, string):
            pass

Post Processors inherit from the abstract base class

    programy.processors.processing.PostProcessor

The class has a single method, process, which takes bot, client and the string to post-process and should return the processed string

    class PostProcessor(Processor):
        def __init__(self):
            Processor.__init__(self)

        @abstractmethod
        def process(self, bot, clientid, string):
            pass
