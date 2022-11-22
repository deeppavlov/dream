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

    go_to_pattern = re.search(
        r"(go to)|(move to)|(come to) (\d+)\,*\s*(\d+)\,*\s*(\d+)",
        utterance,
        re.IGNORECASE,
    )

    stop_pattern = re.search(r"sto+p", utterance, re.IGNORECASE)
    look_at_me_pattern = re.search(r"look (at me)|(here)", utterance, re.IGNORECASE)
    follow_me_pattern = re.search(r"follow me", utterance, re.IGNORECASE)
    remove_block_pattern = re.search(
        r"((remove)|(delete)|(destroy)|(get rid of))(( the)|( this))* block",
        utterance,
        re.IGNORECASE,
    )
    place_block_pattern = re.search(
        r"((place)|(put)|(make))( a)* block", utterance, re.IGNORECASE
    )
    grab_block_pattern = re.search(
        r"((grab)|(get))( a)* block", utterance, re.IGNORECASE
    )
    come_to_me_pattern = re.search(
        r"((come to me)|(go to me))|((come here)|(go here))", utterance, re.IGNORECASE
    )
    come_there_pattern = re.search(
        r"((move there)|(get there))|((come there)|(go there))",
        utterance,
        re.IGNORECASE,
    )
    come_build_house_patterh = re.search(
        r"(build a house)|(build house)|(build a home)|(build home)", utterance, re.IGNORECASE
    )

    recreate_pattern = re.search(
        r"\brecreate\b", utterance, re.IGNORECASE
        )

    start_building_pattern = re.search(
        r"\bstart building\b", utterance, re.IGNORECASE
        )

    finish_building_pattern = re.search(
        r"\bfinish building\b", utterance, re.IGNORECASE
        )

    if come_to_me_pattern:
        answer_probs["goto_user"] = 1.0
        answer_labels.append("goto_user")
    elif come_there_pattern:
        answer_probs["goto_cursor"] = 1.0
        answer_labels.append("goto_cursor")
    elif go_to_pattern:
        answer_probs["goto"] = 1.0
        answer_labels.append("goto")
    elif follow_me_pattern:
        answer_probs["follow_me"] = 1.0
        answer_labels.append("follow_me")
    elif stop_pattern:
        answer_probs["stop"] = 1.0
        answer_labels.append("stop")
    elif remove_block_pattern:
        answer_probs["destroy_block"] = 1.0
        answer_labels.append("destroy_block")
    elif place_block_pattern:
        answer_probs["place_block"] = 1.0
        answer_labels.append("place_block")
    elif grab_block_pattern:
        answer_probs["destroy_and_grab_block"] = 1.0
        answer_labels.append("destroy_and_grab_block")
    elif look_at_me_pattern:
        answer_probs["look_at_user"] = 1.0
        answer_labels.append("look_at_user")
    elif come_build_house_patterh:
        answer_probs["build_house"] = 1.0
    elif recreate_pattern:
        answer_probs["recreate"] = 1.0
        answer_labels.append("recreate")
    elif start_building_pattern:
        answer_probs["start_building"] = 1.0
        answer_labels.append("start_building")
    elif finish_building_pattern:
        answer_probs["finish_building"] = 1.0
        answer_labels.append("finish_building")
    
        

    if len(answer_labels) > 0:
        logger.debug(
            f'Minecraft Bot Intent Catcher: got a "{answer_labels[0]}" command!'
        )
    else:
        logger.debug(f"Minecraft Bot Intent Catcher: got nothing :(")

    return answer_probs, answer_labels
