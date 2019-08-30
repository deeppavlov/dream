from typing import Dict, List, Tuple


class ConfidenceResponseSelector:
    """Select a single response for each dialog turn.
    """

    def __call__(self, state: Dict) -> Tuple[List[str], List[str], List[float]]:
        skill_names = []
        utterances = []
        confidences = []
        responses = [d['utterances'][-1]['selected_skills'] for d in state['dialogs']]
        for r in responses:
            sr = sorted(r.items(), key=lambda x: x[1]['confidence'], reverse=True)[0]
            skill_names.append(sr[0])
            utterances.append(sr[1]['text'])
            confidences.append(sr[1]['confidence'])
        return skill_names, utterances, confidences
