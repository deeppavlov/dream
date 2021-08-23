from common.dialogflow_framework.extensions import custom_functions


art_to_states = {"drawing_q": r"art",
                 ("drawing",): [any, [r"(draw|paint)"]],
                 ("photo",): [all, [r"photo",
                                    custom_functions.speech_functions("Sustain.Continue.Prolong.Extend")]]
                 }
