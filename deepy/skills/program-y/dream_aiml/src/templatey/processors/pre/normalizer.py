from programy.processors.processing import Processor


class PreProcessor(Processor):

    def __init__(self, fpath="./dream_aiml/storage/lookups/normal.txt"):
        Processor.__init__(self)
        self.patterns = []
        with open(fpath, "r") as f:
            self.patterns = f.read().splitlines()
        self.patterns = [raw[1:-1].split('","')for raw in self.patterns]

    def process(self, string):
        for pattern in self.patterns:
            new_string = string.replace(pattern[0], pattern[1])
            if new_string != string:
                string = new_string
        return string
