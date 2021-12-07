import re

import src.data.utils as data_utils
import src.data.atomic as adata
from config import settings

conceptnet_relations = {
    "AtLocation",
    "CapableOf",
    "Causes",
    "CausesDesire",
    "CreatedBy",
    "DefinedAs",
    "DesireOf",
    "Desires",
    "HasA",
    "HasFirstSubevent",
    "HasLastSubevent",
    "HasPainCharacter",
    "HasPainIntensity",
    "HasPrerequisite",
    "HasProperty",
    "HasSubevent",
    "InheritsFrom",
    "InstanceOf",
    "IsA",
    "LocatedNear",
    "LocationOfAction",
    "MadeOf",
    "MotivatedByGoal",
    "NotCapableOf",
    "NotDesires",
    "NotHasA",
    "NotHasProperty",
    "NotIsA",
    "NotMadeOf",
    "PartOf",
    "ReceivesAction",
    "RelatedTo",
    "SymbolOf",
    "UsedFor",
}


def split_camelcase(words):
    splitted = {word: re.sub("(?<=[a-z])(?=[A-Z])", " ", word).lower() for word in words}
    return splitted


split_into_words = split_camelcase(conceptnet_relations)


class GenerationDataLoader(adata.DataLoader):
    def __init__(self, opt):
        super(GenerationDataLoader, self).__init__(opt)
        self.opt = opt

        for split in self.data:
            self.data[split] = {"total": []}
            self.offsets[split] = {"total": 0}

        self.vocab_encoder = None
        self.vocab_decoder = None
        self.special_chars = None
        self.max_e1 = None
        self.max_e2 = None
        self.max_r = None

    def load_data(self, path):
        if ".pickle" in path:
            data_utils.load_existing_data_loader(self, path)
            return True


def make_attention_mask(sequences):
    return (sequences != 0).float().to(settings.device)


def do_example(text_encoder, event1, relation, event2):
    final_event1 = text_encoder.encode([event1], verbose=False)[0]
    if relation.lower() != relation:
        final_relation = [text_encoder.encoder[relation]]
    else:
        final_relation = text_encoder.encode([relation], verbose=False)[0]

    final_event2 = text_encoder.encode([event2], verbose=False)[0] if event2 is not None else None

    return final_event1, final_relation, final_event2
