from typing import Dict

from core.state_schema import Bot, BotUtterance, Dialog, Human, HumanUtterance


class StateManager:
    def __init__(self, db):
        self._db = db

    async def add_human_utterance(self, dialog: Dialog, payload: Dict, label: str, **kwargs) -> None:
        dialog.add_human_utterance()
        dialog.utterances[-1].text = payload
        dialog.utterances[-1].user = dialog.human.to_dict()
        dialog.utterances[-1].attributes = kwargs.get('message_attrs', {})

    async def add_hypothesis(self, dialog: Dialog, payload: Dict, label: str, **kwargs):
        hypothesis = {'skill_name': label, 'annotations': {}}
        for h in payload:
            dialog.utterances[-1].hypotheses.append({**hypothesis, **h})

    async def add_annotation(self, dialog: Dialog, payload: Dict, label: str, **kwargs):
        dialog.utterances[-1].annotations[label] = payload

    async def add_hypothesis_annotation(self, dialog: Dialog, payload: Dict, label: str, **kwargs):
        ind = kwargs['ind']
        dialog.utterances[-1].hypotheses[ind]['annotations'][label] = payload

    async def add_text(self, dialog: Dialog, payload: str, label: str, **kwargs):
        dialog.utterances[-1].text = payload

    async def update_human(self, human: Human, active_skill: Dict):
        attributes = active_skill.get('human_attributes', {})
        for attr_name, attr_value in attributes.items():
            if attr_name in human.to_dict():
                setattr(human, attr_name, attr_value)
            elif attr_name in human.profile:
                human.profile[attr_name] = attr_value
            else:
                human.attributes[attr_name] = attr_value

    async def update_bot(self, bot: Bot, active_skill: Dict):
        attributes = active_skill.get('bot_attributes', {})
        for attr_name, attr_value in attributes.items():
            if attr_name in bot.to_dict():
                setattr(bot, attr_name, attr_value)
            else:
                bot.attributes[attr_name] = attr_value

    async def add_bot_utterance(self, dialog: Dialog, payload: Dict, label: str, **kwargs) -> None:
        await self.update_human(dialog.human, payload)
        await self.update_bot(dialog.bot, payload)
        dialog.add_bot_utterance()
        dialog.utterances[-1].text = payload['text']
        dialog.utterances[-1].active_skill = payload['skill_name']
        dialog.utterances[-1].confidence = payload['confidence']
        dialog.utterances[-1].annotations = payload.get('annotations', {})
        dialog.utterances[-1].user = dialog.bot.to_dict()

    async def add_bot_utterance_last_chance(self, dialog: Dialog, payload: Dict, label: str, **kwargs) -> None:
        if isinstance(dialog.utterances[-1], HumanUtterance):
            dialog.add_bot_utterance()
            dialog.utterances[-1].text = payload['text']
            dialog.utterances[-1].active_skill = label
            dialog.utterances[-1].confidence = 0
            dialog.utterances[-1].annotations = payload['annotations']
            dialog.utterances[-1].user = dialog.bot.to_dict()

    async def add_failure_bot_utterance(self, dialog: Dialog, payload: Dict, label: str, **kwargs) -> None:
        dialog.add_bot_utterance()
        dialog.utterances[-1].text = payload
        dialog.utterances[-1].active_skill = label
        dialog.utterances[-1].confidence = 0
        dialog.utterances[-1].user = dialog.bot.to_dict()

    async def save_dialog(self, dialog: Dialog, payload: Dict, label: str, **kwargs) -> None:
        await dialog.save(self._db)

    async def get_or_create_dialog_by_tg_id(self, user_telegram_id, channel_type):
        return await Dialog.get_or_create_by_ext_id(self._db, user_telegram_id, channel_type)

    async def get_dialog_by_id(self, dialog_id):
        return await Dialog.get_by_id(self._db, dialog_id)

    async def get_dialogs_by_user_ext_id(self, user_telegram_id):
        return await Dialog.get_many_by_ext_id(self._db, user_telegram_id)

    async def get_all_dialogs(self):
        return await Dialog.get_all(self._db)

    async def drop_active_dialog(self, user_telegram_id):
        user = await Human.get_or_create(self._db, user_telegram_id)
        await Dialog.drop_active(self._db, user._id)

    async def prepare_db(self):
        await BotUtterance.prepare_collection(self._db)
        await HumanUtterance.prepare_collection(self._db)
        await Human.prepare_collection(self._db)
        await Dialog.prepare_collection(self._db)

    async def get_channels(self):
        return await Dialog.get_channels(self._db)
