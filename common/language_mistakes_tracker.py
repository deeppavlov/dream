import json
import logging


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class LanguageMistakes:

    def __init__(self, initial_state=None):
        if initial_state:
            initial_state = self.load_dump(initial_state)
            for key, value in initial_state.items():
                setattr(self, key, value)
        else:
            self.state = []
    
    def dump_state(self):
        jsonStr = json.dumps(self.__dict__)
        return jsonStr
    
    def load_dump(self, initial_state: str):
        state_json = json.loads(initial_state)
        return state_json

    def update_language_mistakes_tracker(self, dialog):
        curr_hum_utt_status = []
        if len(dialog["utterances"]) != 1:
            user_utt = dialog["human_utterances"][-2]["text"]
            corrected_utt = dialog["human_utterances"][-2].get("annotations", {}).get("spelling_preprocessing", "")
            logger.info(f"language_mistakes update: {corrected_utt}")
            if corrected_utt != user_utt:
                curr_hum_utt_status.append(
                    {
                        "original_sentence": user_utt,
                        "corrected_sentence": corrected_utt
                    }
                )
                self.state.append(curr_hum_utt_status)