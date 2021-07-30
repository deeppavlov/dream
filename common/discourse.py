import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_speech_function_for_human_utterance_annotations(annotations):
    sfs = annotations.get("speech_function_classifier", {})
    phrases = annotations.get("sentseg", {}).get("segments", [])

    sfunctions = {}
    i = 0
    for phrase in phrases:
        if len(sfs) > i:
            sfunctions[phrase] = sfs[i]
        i = i + 1

    return sfunctions


def get_speech_function_predictions_for_human_utterance_annotations(annotations):
    predicted_sfs = annotations.get("speech_function_predictor", [])
    return predicted_sfs


def get_speech_function_for_bot_utterance_annotations(text, annotations):
    sfs = annotations.get("speech_function_classifier", {})

    if len(sfs) > 0:
        return sfs[0].rstrip('.')

    return None


# Discourse Management-Based Response Selection
def dm_based_response_selection(dialog, candidates):
    annotated_uttr = dialog["human_utterances"][-1]
    # all_user_intents, all_user_topics, all_user_named_entities, all_user_nounphrases = get_main_info_annotations(
    #     annotated_uttr)
    user_uttr_annotations = annotated_uttr["annotations"]

    # obtaining speech functions for all segments of the human's utterance
    # speech_functions_from_user_phrase = get_speech_function_for_human_utterance_annotations(user_uttr_annotations)

    filtered_candidates = []
    proposed_speech_functions = []

    sf_predictions = get_speech_function_predictions_for_human_utterance_annotations(user_uttr_annotations)
    if sf_predictions:
        sf_predictions_list = list(sf_predictions)
        sf_predictions_for_last_phrase = sf_predictions_list[-1]

        # using only last user's phrase
        for sf_prediction in sf_predictions_for_last_phrase:
            if "prediction" in sf_prediction:
                prediction = sf_prediction["prediction"]
                proposed_speech_functions.append(prediction)

    logger.info(f"Response Selector: Proposed Speech Functions: {proposed_speech_functions}")

    # now it's time to understand how SFC classified responses
    for candidate in candidates:
        candidate_annotations = candidate["annotations"]
        candidate_text = candidate["text"]

        candidate_sfc = get_speech_function_for_bot_utterance_annotations(candidate_text, candidate_annotations)

        if candidate_sfc is not None:
            if candidate_sfc in proposed_speech_functions:
                logger.info(f"Speech Function proposed for candidate {candidate_text}: {candidate_sfc}")
                filtered_candidates.append(candidate)

    return filtered_candidates
