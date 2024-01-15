from deeppavlov import build_model


model = build_model("speech_fn")


def check_sfs(predicted_sf, previous_sf, current_speaker, previous_speaker):
    if predicted_sf == "Command":
        if ("Open" in previous_sf or previous_sf == "") and current_speaker == previous_speaker:
            return "Open.Command"
        elif current_speaker == previous_speaker:
            return "Sustain.Continue.Command"
        else:
            return "React.Respond.Command"
    elif predicted_sf == "Engage":
        if previous_sf == "":
            return "Open.Attend"
        else:
            return "React.Respond.Support.Engage"
    return predicted_sf


def get_speech_functions(phrases, prev_phrases, previous_sfs, speakers=None, previous_speakers=None):
    # note: default values for current and previous speaker are only to make them different.
    # In out case they are always
    # different (bot and human)
    speakers = ["john" for _ in phrases]
    previous_speakers = ["doe" for _ in phrases]
    predicted_sfs = model(phrases, prev_phrases)
    result = []
    for pred_sf, prev_sf, speaker, prev_speaker in zip(predicted_sfs, previous_sfs, speakers, previous_speakers):
        result += [check_sfs(pred_sf, prev_sf, speaker, prev_speaker)]
    return result
