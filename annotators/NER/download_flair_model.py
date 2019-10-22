from flair.models import SequenceTagger
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("flair model is loadding ..")
tagger = SequenceTagger.load('ner-ontonotes')
logger.info("flair model is loaded.")
