from typing import List

from deeppavlov.core.models.component import Component


class AnnotationsParser(Component):
    """ Inputs utterance annotations and gets recursive values.

    Example:
        > parser = AnnotaionsParser(keys=['ner.tokens', 'ner.tags'])
        > parser([{'ner': {'tokens': ['I'], 'tags': ['O']}}])
        [['I']], [['O']]
    """

    def __init__(self, keys, **kwargs):
        self.keys = [k.split('.') for k in keys]

    def __call__(self, annotations: List[dict]) -> List[List]:
        ann_values = [[]] * len(self.keys)
        for ann in annotations:
            for i, key_rec in enumerate(self.keys):
                val = ann
                for j in range(len(key_rec)):
                    try:
                        val = val[key_rec[j]]
                    except KeyError:
                        val = []
                ann_values[i] = ann_values[i] + [val]
        return ann_values


class DialogsPersonaParser(Component):
    def __init__(self, **kwargs):
        pass

    def __call__(self, dialogs: List[dict]) -> List[List[str]]:
        bot_personas = []

        for dialog in dialogs:
            bot_personas.append(dialog['bot']['persona'])
        return bot_personas
