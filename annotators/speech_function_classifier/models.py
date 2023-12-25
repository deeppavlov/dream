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


def get_speech_function(phrase, prev_phrase, previous_sf, speaker="John", previous_speaker="Doe"):
    # note: default values for current and previous speaker are only to make them different.
    # In out case they are always
    # different (bot and human)
    predicted_sf = model([phrase], [prev_phrase])
    y_pred = check_sfs(predicted_sf[0], previous_sf, speaker, previous_speaker)
    return y_pred
