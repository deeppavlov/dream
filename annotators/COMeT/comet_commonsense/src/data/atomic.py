import utils.utils as utils
import src.data.utils as data_utils
from config import settings


class DataLoader:
    def __init__(self, opt):
        self.data = {"train": {}, "dev": {}, "test": {}}
        self.sequences = {"train": {}, "dev": {}, "test": {}}
        self.masks = {"train": {}, "dev": {}, "test": {}}
        self.offsets = {"train": {}, "dev": {}, "test": {}}


class GenerationDataLoader(DataLoader):
    def __init__(self, opt, categories):
        super(GenerationDataLoader, self).__init__(opt)

        self.categories = categories
        self.opt = opt

        for split in self.data:
            self.data[split] = {"total": []}
            self.offsets[split] = {"total": 0}

        self.vocab_encoder = None
        self.vocab_decoder = None
        self.special_chars = None
        self.max_event = None
        self.max_effect = None

    def load_data(self, path):
        if ".pickle" in path:
            data_utils.load_existing_data_loader(self, path)
            return True


def make_attention_mask(sequences):
    return (sequences != 0).float().to(settings.device)


def find_underscore_length(seq):
    start = "_"

    while start in seq:
        start += "_"
    return start[:-1]


def handle_underscores(suffix, text_encoder, prefix=False):
    encoder = text_encoder.encoder
    if prefix:
        tok = "___"
    else:
        tok = find_underscore_length(suffix)

    suffix_parts = [i.strip() for i in suffix.split("{}".format(tok))]
    to_flatten = []
    for i, part in enumerate(suffix_parts):
        if part:
            to_flatten.append(text_encoder.encode([part], verbose=False)[0])

            if i != len(suffix_parts) - 1 and suffix_parts[i + 1]:
                to_flatten.append([encoder["<blank>"]])
        else:
            to_flatten.append([encoder["<blank>"]])

    final_suffix = utils.flatten(to_flatten)

    return final_suffix


def do_example(text_encoder, prefix, suffix, do_prefix, do_suffix):
    final_prefix, final_suffix = None, None

    if do_prefix:
        final_prefix = handle_underscores(prefix, text_encoder, True) if "___" in prefix else \
            text_encoder.encode([prefix], verbose=False)[0]

    if do_suffix:
        final_suffix = handle_underscores(suffix, text_encoder) if "_" in suffix else \
            text_encoder.encode([suffix], verbose=False)[0]

    return final_prefix, final_suffix


num_delimiter_tokens = {
    "category": 1,
    "hierarchy": 3,
    "hierarchy+label": 4,
    "category+hierarchy": 4,
    "category+hierarchy+label": 5
}
