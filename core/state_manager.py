from datetime import datetime
from typing import Hashable, Any, Optional, Dict

from core.bot import BOT
from core.state_schema import Human, Bot, HumanUtterance, BotUtterance, Dialog


class StateManager:

    @staticmethod
    def create_new_dialog(user, bot, location=None, channel_type=None):
        dialog = Dialog(user=user,
                        bot=bot,
                        location=location or Dialog.location.default,
                        channel_type=channel_type)
        dialog.save()
        return dialog

    @staticmethod
    def create_new_human(user_telegram_id, device_type, personality=None, profile=None):
        human = Human(user_telegram_id=user_telegram_id,
                      device_type=device_type,
                      personality=personality,
                      profile=profile or Human.profile.default)
        human.save()
        return human

    @staticmethod
    def create_new_human_utterance(text, user, date_time, annotations=None, selected_skills=None):
        if isinstance(user, Bot):
            raise RuntimeError(
                'Utterances of bots should be created with different method. See create_new_bot_utterance()')
        utt = HumanUtterance(text=text,
                             user=user,
                             date_time=date_time,
                             annotations=annotations or HumanUtterance.annotations.default,
                             selected_skills=selected_skills or HumanUtterance.selected_skills.default)
        utt.save()
        return utt

    @staticmethod
    def create_new_bot_utterance(orig_text, text, user, date_time, active_skill, confidence, annotations=None):
        utt = BotUtterance(orig_text=orig_text,
                           text=text,
                           user=user,
                           date_time=date_time,
                           active_skill=active_skill,
                           confidence=confidence,
                           annotations=annotations or BotUtterance.annotations.default)
        utt.save()
        return utt

    @staticmethod
    def update_user_profile(me_user, profile):
        me_user.profile.update(**profile)
        me_user.save()

    # non batch shit

    @classmethod
    def get_or_create_user(cls, user_telegram_id=Hashable, user_device_type=Any):
        user_query = Human.objects(user_telegram_id__exact=user_telegram_id)
        if not user_query:
            user = cls.create_new_human(user_telegram_id, user_device_type)
        else:
            user = user_query[0]
        return user

    @classmethod
    def get_or_create_dialog(cls, user, location, channel_type, should_reset=False):
        if should_reset:
            dialog = cls.create_new_dialog(user=user, bot=BOT, location=location,
                                           channel_type=channel_type)
        else:
            exist_dialogs = Dialog.objects(user__exact=user)
            if not exist_dialogs:
                # TODO remove this "if" condition: it should never happen in production, only while testing
                dialog = cls.create_new_dialog(user=user, bot=BOT, location=location,
                                               channel_type=channel_type)
            else:
                dialog = exist_dialogs[0]

        return dialog

    @classmethod
    def add_human_utterance(cls, dialog: Dialog, text: str, date_time: datetime,
                            annotation: Optional[dict] = None,
                            selected_skill: Optional[dict] = None) -> None:
        utterance = cls.create_new_human_utterance(text, dialog.user, date_time, annotation, selected_skill)
        dialog.utterances.append(utterance)
        dialog.save()

    @classmethod
    def add_bot_utterance(cls, dialog: Dialog, orig_text: str,
                          date_time: datetime, active_skill: str,
                          confidence: float, text: str = None, annotation: Optional[dict] = None) -> None:
        if not text:
            text = orig_text
        utterance = cls.create_new_bot_utterance(orig_text, text, dialog.bot, date_time, active_skill, confidence,
                                                 annotation)
        dialog.utterances.append(utterance)
        dialog.save()

    @staticmethod
    def add_annotation(dialog: Dialog, payload: Dict):
        dialog.utterances[-1].annotations.update(payload)
        dialog.utterances[-1].save()

    @staticmethod
    def add_selected_skill(dialog: Dialog, payload: Dict):
        if not dialog.utterances[-1].selected_skills:
            dialog.utterances[-1].selected_skills = {}
        dialog.utterances[-1].selected_skills.update(payload)
        dialog.utterances[-1].save()

    @staticmethod
    def add_text(dialog: Dialog, payload: str):
        dialog.utterances[-1].text = payload
        dialog.utterances[-1].save()

    @classmethod
    def add_bot_utterance_simple(cls, dialog: Dialog, payload: Dict):
        active_skill_name = list(payload.values())[0]
        active_skill = dialog.utterances[-1].selected_skills.get(active_skill_name, None)
        if not active_skill:
            raise ValueError(f'provided {payload} is not valid')

        text = active_skill['text']
        confidence = active_skill['confidence']

        cls.add_bot_utterance(dialog, text, datetime.now(), active_skill_name, confidence)

    @staticmethod
    def do_nothing(*args, **kwargs):  # exclusive workaround for skill selector
        pass
