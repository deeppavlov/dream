from typing import Dict

from core.state_schema import Bot, Dialog, Human


class StateManager:
    def __init__(self, db):
        self._db = db

    async def add_human_utterance(self, dialog: Dialog, payload: Dict, **kwargs) -> None:
        dialog.add_human_utterance()
        dialog.utterances[-1].text = payload
        dialog.utterances[-1].user = dialog.human.to_dict()
        dialog.utterances[-1].attributes = kwargs.get('message_attrs', {})

    async def add_hypothesis(self, dialog: Dialog, payload: Dict, **kwargs):
        hypothesis = {'skill_name': list(payload.keys())[0]}
        for h in list(payload.values())[0]:
            dialog.utterances[-1].hypotheses.append({**hypothesis, **h})

    async def add_annotation(self, dialog: Dialog, payload: Dict, **kwargs):
        dialog.utterances[-1].annotations.update(payload)

    async def add_text(self, dialog: Dialog, payload: str, **kwargs):
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

    async def add_bot_utterance(self, dialog: Dialog, payload: Dict, **kwargs) -> None:
        rselector_data = list(payload.values())[0]
        new_text = rselector_data['text']
        new_confidence = rselector_data['confidence']
        await self.update_human(dialog.human, rselector_data)
        await self.update_bot(dialog.bot, rselector_data)
        dialog.add_bot_utterance()
        dialog.utterances[-1].text = new_text
        dialog.utterances[-1].active_skill = rselector_data['skill_name']
        dialog.utterances[-1].confidence = new_confidence
        dialog.utterances[-1].user = dialog.bot.to_dict()

    async def save_dialog(self, dialog: Dialog, payload: Dict, **kwargs) -> None:
        await dialog.save(self._db)

    async def get_or_create_dialog_by_tg_id(self, user_telegram_id, channel_type):
        return await Dialog.get_or_create_by_ext_id(self._db, user_telegram_id, channel_type)

    async def do_nothing(self, dialog: Dialog, payload: Dict, **kwargs) -> None:
        pass

    async def get_dialog_by_id(self, dialog_id):
        return await Dialog.get_by_id(self._db, dialog_id)

    async def drop_active_dialog(self, user_telegram_id):
        user = await Human.get_or_create(self._db, user_telegram_id)
        await Dialog.drop_active(self._db, user._id)
