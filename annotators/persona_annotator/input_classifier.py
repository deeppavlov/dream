import pandas as pd
import gensim.downloader
from random import choices
from nltk import word_tokenize
from deeppavlov.core.common.registry import register
from overrides import overrides
import logging

OCEAN = {'openness': True,
         'conscientiousness': True,
         'extraversion': False,
         'neuroticism': True,
         'agreeableness': False}
interests = {'smoking': True,
             'music': True,
             'family': False,
             'chemistry': True,
             'crime': True,
             'beekeeping': True,
             'combat': True}
# hand-crafted for now, can be collected automatically from text:
related_entities = {'Sherlock': 'Q4653',
                    'London': 'Q84',
                    'England': 'Q21',
                    'United Kingdom': 'Q145',
                    'Great Britain': 'Q23666',
                    'Baker street': 'Q804402',
                    'Scotland Yard': 'Q184619',
                    'Watson': 'Q187349',
                    'Hudson': 'Q2456753',
                    'Mycroft': 'Q1616457',
                    'Moriarty': 'Q283111'}

corpus = pd.read_csv('data/bbc-text.csv').text.tolist()

vectors = gensim.downloader.load('glove-wiki-gigaword-300')
# synonyms = Classifier.collect_synonyms(interests)


@register("persona_annotator")
class InputClassifier:
    def __init__(self, sentences):
        pass

    @staticmethod
    def collect_synonyms(interests_dict):
        """collects 20 closest quasi-synonyms for each word"""
        synonyms_dict = {}
        for word in interests_dict.keys():
            synonyms_dict[word] = [pair[0] for pair in vectors.most_similar(word, topn=20)]
            synonyms_dict[word].append(word)
        return synonyms_dict

    @staticmethod
    def get_angry():
        """if a character is neurotic func throws a tantrum with 11% chance"""
        print('--starting get_angry()')
        if OCEAN['neuroticism']:
            return choices([True, False], [0.11, 0.89])[0]
        return False

    def is_news(self):
        """checks if input looks like a news article"""
        print('--starting is_news()')
        if self.sentences in corpus:  # to be replaced with any existing classifier
            return True
        return False

    def interesting_topic(self):
        """checks if an article matches character interests"""
        print('--starting interesting_topic()')
        topics = []
        tokens = word_tokenize(self.sentences)
        for topic in self.synonyms.keys():
            intersect = set(tokens) & set(self.synonyms[topic])
            if len(intersect) != 0:
                topics.append(topic)

        # add to topics if entity is in character's list
        for entity in related_entities.keys():
            # to be replaced with entity linking + data from dialog formatter[1]['annotations']
            if entity in tokens:  # input tokens
                topics.append(entity)
        return topics

    @overrides
    def __call__(self, sentences, annotations):
        """main function"""
        self.sentences = sentences
        self.synonyms = self.collect_synonyms(interests)

        logging.info(sentences)
        print('--starting if_answer()')
        ga_state = self.get_angry()
        print(f'get_angry state {ga_state}')
        if ga_state:  # if get_angry():
            result = ["temper_tantrum"]  # можно заменить на набор настоящих фраз раздражённого шерлока из книг
        else:
            if self.is_news():
                topics = self.interesting_topic()
                if topics:
                    result = ["interesting", topics]
                else:
                    result = ["not_interesting"]
            else:
                result = ["not_news"]

        logging.info(result)
        return result
