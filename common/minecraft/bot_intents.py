import logging
import re

logger = logging.getLogger(__name__)

def detect_minecraft_bot_intents(utterance):
    logger.debug(f"Minecraft Bot Intent Catcher: checking for supported commands!")

    # stop - остановить действие
    # look at me - посмотреть
    # follow me - следовать за игроком
    # place block here - поставить блок
    # remove this block - убрать
    # grab block

    answer_probs = {}
    answer_labels = []

    GO_TO_PATTERN = re.search(r"(go to)|(move to)|(come to) (\d+)\,*\s*(\d+)\,*\s*(\d+)", utterance, re.IGNORECASE)
    
    STOP_PATTERN = re.search(r"sto+p", utterance, re.IGNORECASE)
    LOOK_AT_ME_PATTERN = re.search(r"look (at me)|(here)", utterance, re.IGNORECASE)
    FOLLOW_ME_PATTERN = re.search(r"follow me", utterance, re.IGNORECASE)
    REMOVE_BLOCK_PATTERN = re.search(r"((remove)|(delete)|(destroy)) ((the)|(this))* block", utterance, re.IGNORECASE)
    PLACE_BLOCK_PATTERN = re.search(r"((place)|(put)|(make))( a)* block", utterance, re.IGNORECASE)
    GRAB_BLOCK_PATTERN = re.search(r"((grab)|(get))( a)* block", utterance, re.IGNORECASE)
    COME_HERE_PATTERN = re.search(r"((come here)|(come to me))|((go here)|(go to me))", utterance, re.IGNORECASE)

    
    
    if COME_HERE_PATTERN:
        answer_probs["goto_user"] = (1.0)
        answer_labels.append("goto_user")
    elif GO_TO_PATTERN:
        answer_probs["goto"] = (1.0)
        answer_labels.append("goto")
    elif FOLLOW_ME_PATTERN:
        answer_probs["follow_me"] = (1.0)
        answer_labels.append("follow_me")
    elif STOP_PATTERN:
        answer_probs["stop"] = (1.0)
        answer_labels.append("stop")
    elif REMOVE_BLOCK_PATTERN:
        answer_probs["destroy_block"] = (1.0)
        answer_labels.append("destroy_block")
    elif PLACE_BLOCK_PATTERN:
        answer_probs["place_block"] = (1.0)
        answer_labels.append("place_block")
    elif GRAB_BLOCK_PATTERN:
        answer_probs["destroy_and_grab_block"] = (1.0)
        answer_labels.append("destroy_and_grab_block")
    elif LOOK_AT_ME_PATTERN:
        answer_probs["look_at_user"] = (1.0)
        answer_labels.append("look_at_user")

    if len(answer_labels)>0:
        logger.debug(f"Minecraft Bot Intent Catcher: got a \"{answer_labels[0]}\" command!")
    else:
        logger.debug(f"Minecraft Bot Intent Catcher: got nothing :(")


    return answer_probs, answer_labels
