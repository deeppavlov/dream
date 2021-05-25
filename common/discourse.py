def get_speech_function_for_human_utterance_annotations(annotations):
    sfs = annotations.get("speech_function_classifier", {})
    phrases = annotations.get("sentseg", {}).get("segments", {})

    sfunctions = {}
    i = 0
    for phrase in phrases:
        if len(sfs)>i:
            sfunctions[phrase] = sfs[i]
        i = i+1

    return sfunctions


def get_speech_function_predictions_for_human_utterance_annotations(annotations):
    predicted_sfs = annotations.get("speech_function_predictor", [])
    return predicted_sfs