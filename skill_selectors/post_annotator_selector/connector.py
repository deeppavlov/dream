from typing import Dict, Callable


class PostAnnotatorSelectorConnector:
    def __init__(self, annotator_names):
        self.annotator_names = set(annotator_names)

    async def send(self, payload: Dict, callback: Callable):
        try:
            if payload['payload']['bot_utterances']:
                existing_annotators = set(payload['payload']['bot_utterances'][-1]['annotations'].keys())
                response = list(self.annotator_names - existing_annotators)
            else:
                response = []
            await callback(
                task_id=payload['task_id'],
                response=response
            )
        except Exception as e:
            response = e
            await callback(
                task_id=payload['task_id'],
                response=response
            )
