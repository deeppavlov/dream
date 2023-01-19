import logging
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
import random
import warnings

logger = logging.getLogger(__name__)
nltk.download("averaged_perceptron_tagger")
nltk.download("punkt")
warnings.simplefilter("ignore")
lmtzr = nltk.WordNetLemmatizer()


def get_all_possible_entities(entity_name):
    entities = []
    ppl = [
        "woman",
        "women",
        "man",
        "men",
        "baby",
        "toddler",
        "people",
        "girl",
        "boy",
        "person",
        "human",
        "lady",
        "gentlemen",
    ]
    if entity_name == "food":
        entities = list(
            set([w for s in wn.synset(f"{entity_name}.n.02").closure(lambda s: s.hyponyms()) for w in s.lemma_names()])
        )
        entities = [ent.replace("_", " ") for ent in entities]
        entities = [ent for ent in entities if ent not in ppl]
    elif entity_name == "person":
        entities = ppl
    elif entity_name == "animal":
        entities = list(
            set([w for s in wn.synset(f"{entity_name}.n.01").closure(lambda s: s.hyponyms()) for w in s.lemma_names()])
        )
        entities = [ent.replace("_", " ") for ent in entities]
        entities = [ent for ent in entities if ent not in ppl]
    else:
        return entities
    return entities


def extract_entity(sentence, entity_name):
    try:
        tokens = [lmtzr.lemmatize(token) for token in word_tokenize(sentence)]
        entities = list(set(entity_name).intersection(tokens))
        return random.choice(entities)
    except IndexError:
        return ""
    return ""


def extract_verb_from_sentence(sentence):
    pos_tagged = nltk.pos_tag(word_tokenize(str(sentence)))
    verbs = list(filter(lambda x: x[1] in ["VB", "VBP", "VBZ", "VBD", "VBN", "VBG"], pos_tagged))
    try:
        if len(verbs) > 0:
            return random.choice(verbs)[0]
    except IndexError:
        return ""
    return ""
