import os

import gensim
from gensim.utils import simple_preprocess
from nltk.stem import WordNetLemmatizer, SnowballStemmer

from src.consts import (
    SubtopicSummaryType,
    LDA_SUBTOPIC_KEY_WORDS_PATH,
    LDA_SUBTOPIC_KEY_PHRASES_PATH,
    LDA_SUBTOPIC_N_WORDS_PATH,
    LDA_SUBTOPIC_SENTENCE_PATH,
    SUBTOPIC_SUMMARY_TYPE,
    MAX_SUBTOPICS_NUM,
    N_BASE_UNIGRAMS,
    N_PARAMETER,
)
from src.utils import load


stemmer = SnowballStemmer("english")


topic2original_topic = {
    "Arts & Entertainment": [
        "Arts & Entertainment",
        "Multimedia",
        "Arts and Living",
        "Entertainment",
        "Arts and Living_Books",
        "Arts and Living_Food and Dining",
        "BookWorld",
        "Arts and Living_Movies",
        "Arts and Living_Home and Garden",
        "Arts and Living_Music",
        "Arts and Living_Travel",
        "Style",
    ],
    "Business": [
        "Business",
        "Business_U.S. Economy",
        "Economy",
        "Capital Business",
        "National-Economy",
        "Business_Metro Business",
        "Economic Policy",
    ],
    "By The Way - Travel": ["By The Way - Travel", "Travel"],
    "Climate & Environment": ["Climate & Environment", "Capital Weather Gang", "Animals", "Climate Solutions"],
    "D.C., Md. & Va.": ["D.C., Md. & Va."],
    "Discussions": ["Discussions", "Live Discussions"],
    "Education": [
        "Education",
        "Higher Education",
        "High Schools",
        "Colleges",
        "KidsPost",
        "The Answer Sheet",
        "Parenting",
    ],
    "Health": ["Health", "Health_Wires", "Health & Science", "Health-Environment-Science", "National/health-science"],
    "History": ["History", "Made by History", "Retropolis"],
    "Immigration": ["Immigration"],
    "Lifestyle": [
        "Lifestyle",
        "LocalLiving",
        "Lifestyle/food",
        "Food",
        "Local",
        "Obituaries",
        "Local-Enterprise",
        "The Extras_Montgomery",
        "The Extras_Southern Md.",
        "The Extras_Fairfax",
        "Morning Mix",
        "Going Out Guide",
        "Weekend",
        "Lifestyle/magazine",
        "Internet Culture",
        "Pop Culture",
        "Inspired Life",
        "PostEverything",
        "Magazine",
        "Lifestyle/style",
        "Brand-studio",
    ],
    "Live Chats": ["Live Chats"],
    "National": ["National", "Nation", "Nationals & MLB", "National-Enterprise"],
    "National Security": ["National Security", "National-Security", "Crime", "Cops-Courts", "True Crime", "Military"],
    "Opinions": [
        "Opinions",
        "Editorial-Opinion",
        "Opinions_Columnists",
        "Opinions_Feedback",
        "Local Opinions",
        "Global Opinions",
        "Opinions_Columns and Blogs",
        "Post Opinión",
        "Opinions/global-opinions",
        "The Plum Line",
        "Fact Checker",
    ],
    "Outlook": ["Outlook"],
    "Photography": ["Photography"],
    "Podcasts": ["Podcasts"],
    "Politics": [
        "Politics",
        "National-Politics",
        "Local-Politics",
        "Politics_Federal Page",
        "Monkey Cage",
        "Politics_Elections",
        "World_Middle East_Iraq",
        "Powerpost",
        "powerpost",
        "The Fix",
    ],
    "Public Relations": [
        "Public Relations",
        "The Extras_Prince William",
        "The Extras_Prince George's",
        "The Extras_Loudoun",
    ],
    "Real Estate": ["Real Estate", "RealEstate"],
    "Religion": ["Religion", "OnFaith"],
    "Science": ["Science"],
    "Sports": [
        "Sports",
        "Sports_High Schools",
        "High School Sports",
        "Sports_Redskins",
        "Redskins",
        "Sports_MLB",
        "Sports_Nationals",
        "Sports_Wizards",
        "Sports_NFL",
        "Sports_NBA",
        "Sports_Capitals",
        "NFL",
        "NBA",
        "College Sports",
        "MLB",
        "Washington Nationals",
        "D.C. Sports Bog",
        "Golf",
        "Soccer",
        "NHL",
        "Fantasy Sports",
        "Esports",
    ],
    "Tablet": ["Tablet"],
    "Technology": [
        "Technology",
        "Technology_Personal Tech",
        "Technology_Special Reports_Satellite Radio",
        "Tech Policy",
        "Innovations",
    ],
    "Topics": ["Topics"],
    "Transportation": [
        "Transportation",
        "Metro_Obituaries",
        "Metro_Virginia",
        "Metro_The District",
        "Gridlock",
        "Metro_Crime",
        "Metro_Maryland",
        "Metro_Maryland_Montgomery",
        "Future of Transportation",
        "Metro_Maryland_Pr. George's",
        "Metro",
        "Cars",
        "Development-Transportation",
    ],
    "U.S. Policy": ["U.S. Policy"],
    "Utils": ["Utils", "Express", "Print_A Section", "Print", "Print_Editorial Pages", "Print_Style	Print_Weekend"],
    "Video Games": ["Video Games", "Video Game News", "Video Gaming"],
    "Washington Post Live": [
        "Washington Post Live",
        "Washington Post Magazine",
        "Washington Post PR Blog",
        "The Washington Post Magazine",
        "Washington Wizards",
        "Washington Capitals",
    ],
    "World": ["World", "Foreign", "World_Asia/Pacific", "Europe", "Asia", "Africa"],
}

original_topic2topic = {v: k for k, vs in topic2original_topic.items() for v in vs}


def load_subtopic_summaries():
    type2path = {
        SubtopicSummaryType.KEY_WORDS: LDA_SUBTOPIC_KEY_WORDS_PATH,
        SubtopicSummaryType.KEY_PHRASES: LDA_SUBTOPIC_KEY_PHRASES_PATH,
        SubtopicSummaryType.N_WORDS: LDA_SUBTOPIC_N_WORDS_PATH,
        SubtopicSummaryType.SENTENCE: LDA_SUBTOPIC_SENTENCE_PATH,
    }
    return load(type2path[SUBTOPIC_SUMMARY_TYPE])


def remove_file(path):
    if os.path.isfile(path):
        os.remove(path)


def remove_subtopic_summaries():
    remove_file(LDA_SUBTOPIC_KEY_WORDS_PATH)
    remove_file(LDA_SUBTOPIC_KEY_PHRASES_PATH)
    remove_file(LDA_SUBTOPIC_N_WORDS_PATH)
    remove_file(LDA_SUBTOPIC_SENTENCE_PATH)


def check_parameters(parameters):
    if (
        parameters is not None
        and parameters["max_subtopic_num"] == MAX_SUBTOPICS_NUM
        and parameters["n_base_unigrams"] == N_BASE_UNIGRAMS
        and parameters["n_parameter"] == N_PARAMETER
    ):
        return parameters
    return None


def get_parameters():
    parameters = {"max_subtopic_num": MAX_SUBTOPICS_NUM, "n_base_unigrams": N_BASE_UNIGRAMS, "n_parameter": N_PARAMETER}
    return parameters


def lemmatize_stemming(text):
    return stemmer.stem(WordNetLemmatizer().lemmatize(text, pos="v"))


def paired(text):
    if len(text) > 1:
        text = [t1 + " " + t2 for t1, t2 in zip(text[:-1], text[1:])]
    return text


def preprocess(word):
    result = [
        lemmatize_stemming(token)
        for token in simple_preprocess(word, min_len=4)
        if token not in gensim.parsing.preprocessing.STOPWORDS
    ]
    result = result[0] if result else ""
    return result
