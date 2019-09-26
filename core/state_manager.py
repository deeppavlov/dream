from datetime import datetime
from typing import Hashable, Any, Optional, Dict, TypeVar, List

from mongoengine import connect

from core.state_schema import User, Human, Bot, HumanUtterance, BotUtterance, Dialog, HUMAN_UTTERANCE_SCHEMA,\
    BOT_UTTERANCE_SCHEMA
from core.transform_config import DB_HOST, DB_PORT, DB_NAME
import logging
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


userT = TypeVar('userT', bound=User)


class StateManager:

    state_storage = connect(host=DB_HOST, port=int(DB_PORT), db=DB_NAME)

    @staticmethod
    def create_new_dialog(human, bot, location=None, channel_type=None):
        dialog = Dialog(human=human, bot=bot, location=location or Dialog.location.default,
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
    def create_new_bot(persona: Optional[List[str]] = None):
        bot = Bot()
        if persona:
            bot.persona = persona
        bot.save()
        return bot

    @staticmethod
    def create_new_human_utterance(text, user: Human, date_time, annotations=None,
                                   selected_skills=None):
        utt = HumanUtterance(text=text,
                             user=user.to_dict(),
                             date_time=date_time,
                             annotations=annotations or HumanUtterance.annotations.default,
                             selected_skills=selected_skills or HumanUtterance.selected_skills.default)
        utt.save()
        return utt

    @staticmethod
    def create_new_bot_utterance(orig_text, text, user, date_time, active_skill, confidence,
                                 annotations=None):
        utt = BotUtterance(orig_text=orig_text,
                           text=text,
                           user=user,
                           date_time=date_time,
                           active_skill=active_skill,
                           confidence=confidence,
                           annotations=annotations or BotUtterance.annotations.default)
        utt.save()
        return utt

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
            bot = cls.create_new_bot()
            dialog = cls.create_new_dialog(human=user, bot=bot, location=location,
                                           channel_type=channel_type)
        else:
            exist_dialogs = Dialog.objects(human__exact=user)
            if not exist_dialogs:
                bot = cls.create_new_bot()
                dialog = cls.create_new_dialog(human=user, bot=bot, location=location,
                                               channel_type=channel_type)
            else:
                dialog = exist_dialogs[0]

        return dialog

    @classmethod
    def add_human_utterance(cls, dialog: Dialog, user: Human, text: str, date_time: datetime,
                            annotation: Optional[dict] = None,
                            selected_skill: Optional[dict] = None) -> None:
        utterance = cls.create_new_human_utterance(text, user, date_time, annotation,
                                                   selected_skill)
        dialog.utterances.append(utterance)
        dialog.save()

    @classmethod
    def add_bot_utterance(cls, dialog: Dialog, orig_text: str,
                          date_time: datetime, active_skill: str,
                          confidence: float, text: str = None,
                          annotation: Optional[dict] = None) -> None:
        if not text:
            text = orig_text
        try:
            bot = dialog.utterances[-2].user
        except IndexError:
            bot = cls.create_new_bot()
        utterance = cls.create_new_bot_utterance(orig_text, text, bot, date_time, active_skill,
                                                 confidence,
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
    def add_bot_response(cls, dialog: Dialog, payload: Dict):
        active_skill_name = list(payload.values())[0]
        human_utterance = dialog.utterances[-1]
        active_skill = human_utterance.selected_skills.get(active_skill_name, None)
        if not active_skill:
            raise ValueError(f'provided {payload} is not valid')

        text = active_skill['text']
        confidence = active_skill['confidence']

        cls.add_bot_utterance(dialog, text, datetime.now(), active_skill_name, confidence)
        cls.update_human(human_utterance.user, active_skill)
        cls.update_bot(dialog.utterances[-1].user, active_skill)

    @staticmethod
    def do_nothing(*args, **kwargs):  # exclusive workaround for skill selector
        pass

    @staticmethod
    def update_human(human: Human, active_skill: Dict):
        attributes = active_skill.get('human_attributes', [])
        profile = human.profile
        if attributes:
            for attr_name in attributes:
                attr_value = active_skill['human_attributes'][attr_name]
                if hasattr(human, attr_name):
                    setattr(human, attr_name, attr_value)
                else:
                    if attr_name in profile.keys():
                        profile[attr_name] = attr_value
                    else:
                        human.attributes[attr_name] = attr_value
        human.save()

    @staticmethod
    def update_bot(bot: Bot, active_skill: Dict):
        attributes = active_skill.get('bot_attributes', [])
        if attributes:
            for attr_name in attributes:
                attr_value = active_skill['bot_attributes'][attr_name]
                if hasattr(bot, attr_name):
                    setattr(bot, attr_name, attr_value)
                else:
                    bot.attributes[attr_name] = attr_value
        bot.save()

    @classmethod
    def add_human_utterance_simple_dict(cls, dialog: Dict, dialog_object: Dialog, payload: Dict,
                                        **kwargs) -> None:
        utterance = HUMAN_UTTERANCE_SCHEMA
        utterance['text'] = payload
        utterance['date_time'] = str(datetime.now())
        utterance['user'] = dialog['human']
        dialog['utterances'].append(utterance)

    @staticmethod
    def update_human_dict(human: Dict, active_skill: Dict):
        attributes = active_skill.get('human_attributes', {})
        for attr_name, attr_value in attributes.items():
            if attr_name in human:
                human[attr_name] = attr_value
            elif attr_name in human['profile']:
                human['profile'][attr_name] = attr_value
            else:
                human['attributes'][attr_name] = attr_value

    @staticmethod
    def update_bot_dict(bot: Dict, active_skill: Dict):
        attributes = active_skill.get('bot_attributes', {})
        for attr_name, attr_value in attributes.items():
            if attr_name in bot:
                bot[attr_name] = attr_value
            else:
                bot['attributes'][attr_name] = attr_value

    @classmethod
    def add_bot_utterance_simple_dict(cls, dialog: Dict, dialog_object: Dialog, payload: Dict,
                                      **kwargs) -> None:
        rselector_data = list(payload.values())[0]
        active_skill_name = rselector_data['skill_name']
        new_text = rselector_data['text']
        new_confidence = rselector_data['confidence']
        active_skill = dialog['utterances'][-1]['selected_skills'].get(active_skill_name, None)
        if not active_skill:
            raise ValueError(f'provided {payload} is not valid')
        cls.update_human_dict(dialog['human'], active_skill)
        cls.update_bot_dict(dialog['bot'], active_skill)

        utterance = BOT_UTTERANCE_SCHEMA
        utterance['text'] = new_text
        utterance['orig_text'] = active_skill['text']
        utterance['date_time'] = str(datetime.now())
        utterance['active_skill'] = active_skill_name
        utterance['confidence'] = new_confidence
        utterance['user'] = dialog['bot']
        dialog['utterances'].append(utterance)

    @staticmethod
    def add_annotation_dict(dialog: Dict, dialog_object: Dialog, payload: Dict, **kwargs):
        dialog['utterances'][-1]['annotations'].update(payload)

    @staticmethod
    def add_selected_skill_dict(dialog: Dict, dialog_object: Dialog, payload: Dict, **kwargs):
        dialog['utterances'][-1]['selected_skills'].update(payload)

    @staticmethod
    def add_text_dict(dialog: Dict, payload: str):
        dialog['utterances'][-1]['text'] = payload

    @staticmethod
    def save_dialog_dict(dialog: Dict, dialog_object: Dialog, payload=None):
        utt_objects = []
        for utt in dialog['utterances'][::-1]:
            if not utt['id']:
                if utt['user']['user_type'] == 'human':
                    utt_objects.append(HumanUtterance.make_from_dict(utt))
                elif utt['user']['user_type'] == 'bot':
                    utt_objects.append(BotUtterance.make_from_dict(utt))
                else:
                    raise ValueError('unknown user type in the utterance')
            else:
                break
        for utt in utt_objects[::-1]:
            utt.save()
            dialog_object.utterances.append(utt)

        dialog_object.human.update_from_dict(dialog['human'])
        dialog_object.bot.update_from_dict(dialog['bot'])
        dialog_object.human.save()
        dialog_object.bot.save()

        dialog_object.save()
