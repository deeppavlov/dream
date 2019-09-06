from typing import Dict, List


class ConfidenceResponseSelector:
    """Select a single response for each dialog turn.
    """

    def __call__(self, state: Dict) -> List[Dict[str, List[str]]]:
        skill_names = []
        responses = [d['utterances'][-1]['selected_skills'] for d in state['dialogs']]
        for r in responses:
            sr = sorted(r.items(), key=lambda x: x[1]['confidence'], reverse=True)[0]
            skill_names.append(sr[0])
        return [{'confidence_response_selector': sn} for sn in skill_names]
