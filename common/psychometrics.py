import statistics
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def is_introvert(dialog):
    is_extravert_across_five_turns = []

    # we need to get five first turns
    human_utterances = dialog["human_utterances"]

    first_5 = human_utterances[:5]

    for human_utterance in first_5:
        user_uttr_annotations = human_utterance["annotations"]

        # Extraversion (outgoing/energetic vs. solitary/reserved)
        # is_extravert = -1
        # Neuroticism (sensitive/nervous vs. secure/confident)
        # is_neu = -1
        # Extraversion (outgoing/energetic vs. solitary/reserved)
        # is_agr = -1
        # Conscientiousness (efficient/organized vs. easy-going/careless)
        # is_con = -1
        # Openness to experience (inventive/curious vs. consistent/cautious)
        # is_opn = -1

        personality_detection = user_uttr_annotations.get("personality_detection", {})

        logger.info(f"personality_detection: {personality_detection}")

        if len(personality_detection) == 5:
            is_extravert = personality_detection[0]

            is_extravert_across_five_turns.append(is_extravert)

    is_extravert_across_five_turns_median = statistics.median(is_extravert_across_five_turns)

    logger.info(f"is_extravert (across first five turns): {is_extravert_across_five_turns_median}")

    if is_extravert_across_five_turns_median > 0.8:
        return True

    return False
