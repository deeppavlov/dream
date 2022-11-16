import re
import json
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet
from common.universal_templates import COMPILE_LETS_TALK_ABOUT_TOPIC

GET_RECOMMENDATION_CERTAIN_PATTERN = r"""((what|which).*(options|to choose|should|can I|would you|recommend|suggest|(is|are).*(best|good|nice|interesting|cheap|expensive)))|recommend me|\
    |suggest me|help me .* choose|need .* recommendation|need .* suggestion|you know any|you have any|is there a|should i"""

GET_RECOMMENDATION_VAGUE_PATTERN = r"""(i wanna|i want to|i('d| would) (like|love)|(cannot|can'*t) choose|any.*ideas.*)\?"""

GET_RECOMMENDATION_PATTERN = re.compile('|'.join([GET_RECOMMENDATION_CERTAIN_PATTERN, GET_RECOMMENDATION_VAGUE_PATTERN]), re.IGNORECASE)

CHAT_ABOUT_EXPLICIT = re.compile(r"""(let's|let us|i wanna|i want to|i('d| would) (like|love) to) |^(chat|discuss|talk about)""", re.IGNORECASE)

WHAT_IS_QUESTION = re.compile(r'what is|what does .* mean|what\?|what do you mean|what are', re.IGNORECASE)

hypotheses_reco = ['I wanna watch a movie. Which one should I choose?',
"Help me choose a movie to watch",
"I want to do something but I don't know what... What do you think?", #???
"I need a book recommendation.",
"Which movie should I watch?", 
"What are the best queer books?",
"Do you know any popular science books about eels?",
"i want to read a new york times bestseller", #problematic
"What can I cook if I only have 2 eggs, milk, onion, mango, flour?",
"Do you have any unusual salad ideas?",
"what are the best restaurants in my area?",
"What is a 4+ star reviews cheap restaurant in my neighbourhood?",
"i have a sore throat. what should i do?",
"recommend me a movie",
"Do you know any good movies?",
"recommend me",
"suggest me"
]

# for hypothesis in hypotheses_reco:
#     print(bool(re.search(GET_RECOMMENDATION_PATTERN, hypothesis)), re.search(GET_RECOMMENDATION_PATTERN, hypothesis))

# syns = wordnet.synsets('agua')
# print(syns[0].definition())

# print(bool(re.search(WHAT_IS_QUESTION, 'what is a bear?')))