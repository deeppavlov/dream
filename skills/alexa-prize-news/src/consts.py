from enum import Enum
from pathlib import Path


class SubtopicSummaryType(Enum):
    KEY_WORDS = "key-words"
    KEY_PHRASES = "key-phrases"
    N_WORDS = "n-words"
    SENTENCE = "sentence"


HOST = "0.0.0.0"
PORT = 3672

ROOT_PATH = str(Path(__file__).parent)

DATA_PATH = ROOT_PATH + "/../data/posts*.json"
LOGS_PATH = ROOT_PATH + "/../AlexaPrize.log"
UPDATER_LOGS_PATH = ROOT_PATH + "/../Updater.log"
HISTORY_DB_PATH = ROOT_PATH + "/../AlexaPrize_chat_history.db"

MODELS_PATH = ROOT_PATH + '/../news_models_files/'

MODELS_INFO_PATH = MODELS_PATH + "models.info"

TF_IDF_MODEL_TMP_PATH = MODELS_PATH + "files"
TF_IDF_MODEL_READER_PATH = MODELS_PATH + "tf_idf_model_reader.db"
TF_IDF_MODEL_CHAINER_PATH = MODELS_PATH + "tf_idf_model_chainer.npz"
TF_IDF_MODEL_CONFIG_PATH = ROOT_PATH + "/model/config.json"

LDA_PATH = MODELS_PATH
LDA_PARAMETERS_PATH = LDA_PATH + "lda_parameters.dict"
LDA_MODEL_PATH = LDA_PATH + "lda.model"
LDA_DICT_PATH = LDA_PATH + "lda_dictionary.dict"
LDA_SUBTOPICS_PATH = LDA_PATH + "lda_subtopics.dict"
LDA_SUBTOPIC_KEY_WORDS_PATH = LDA_PATH + "lda_summaries_key_words.dict"
LDA_SUBTOPIC_KEY_PHRASES_PATH = LDA_PATH + "lda_summaries_key_phrases.dict"
LDA_SUBTOPIC_N_WORDS_PATH = LDA_PATH + "lda_summaries_n_words.dict"
LDA_SUBTOPIC_SENTENCE_PATH = LDA_PATH + "lda_summaries_sentence.dict"

UPDATE_ON_START = False
UPDATE_PERIOD = 1 * 60 * 60  # 1 hours

NUM_NEWS_TO_PRINT = 1  # Number of latest news to propose
MIN_LEVENSHTEIN_DISTANCE = 2  # Min levenshtein distance for all spell corrections

# TF_IDF model parameters (headline search)
FIRST_SIMILARITY_THRESHOLD = 50  # score first predicted news should have to be printed
SIMILARITY_THRESHOLD = 20  # score last (NUM_NEWS_TO_PRINT) predicted news should have to be printed

# LDA models parameters (topic modeling)
MAX_SUBTOPICS_NUM = 3  # Max number of subtopics in a topic

# Subtopic summary parameters
SUBTOPIC_SUMMARY_TYPE = SubtopicSummaryType.N_WORDS  # Type of subtopic summary
N_BASE_UNIGRAMS = 5  # Number of top unigrams from LDA to consider for summary
N_PARAMETER = 5  # Parameter for subtopic summaries
