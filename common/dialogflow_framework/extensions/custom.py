import logging
import re
from common.dialogflow_framework.extensions import custom_functions


logger = logging.getLogger(__name__)

art_to_states = {
    ("art", "drawing_q"): "art",
    ("drawing", "what_painter"): [any, [re.compile("(draw|paint)")]],
    ("photo", "what_photos"): [all, ["photo", custom_functions.speech_functions("Sustain.Continue.Prolong.Extend")]],
}
