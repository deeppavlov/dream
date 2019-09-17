import uuid

from mongoengine import DynamicDocument, ReferenceField, ListField, StringField, DynamicField, \
    DateTimeField, FloatField, DictField, ObjectIdField

from . import STATE_API_VERSION


class User(DynamicDocument):
    persona = ListField(default=[])
    attributes = DictField()

    meta = {'allow_inheritance': True}

    def to_dict(self):
        raise NotImplementedError


class Bot(User):

    def to_dict(self):
        return {'id': str(self.id),
                'user_type': 'bot',
                'persona': self.persona,
                'attributes': str(self.attributes)
                }


class Human(User):
    user_telegram_id = StringField(required=True, unique=True, sparse=True)
    device_type = DynamicField()
    profile = DictField(required=True, default={
        "name": None,
        "gender": None,
        "birthdate": None,
        "location": None,
        "home_coordinates": None,
        "work_coordinates": None,
        "occupation": None,
        "income_per_year": None
    })

    def to_dict(self):
        return {'id': str(self.id),
                'user_telegram_id': str(self.user_telegram_id),
                'user_type': 'human',
                'device_type': self.device_type,
                'persona': self.persona,
                'profile': self.profile,
                'attributes': str(self.attributes)
                }


class Utterance(DynamicDocument):
    text = StringField(required=True)
    annotations = DictField(default={})
    user = ReferenceField(User, required=True)
    date_time = DateTimeField(required=True)

    meta = {'allow_inheritance': True}

    def to_dict(self):
        raise NotImplementedError


class HumanUtterance(Utterance):
    selected_skills = DynamicField(default=[])

    def to_dict(self):
        return {'id': str(self.id),
                'text': self.text,
                'user': self.user.to_dict(),
                'annotations': self.annotations,
                'date_time': str(self.date_time),
                'selected_skills': self.selected_skills}


class BotUtterance(Utterance):
    orig_text = StringField()
    active_skill = StringField()
    confidence = FloatField()

    def to_dict(self):
        return {
            'id': str(self.id),
            'active_skill': self.active_skill,
            'confidence': self.confidence,
            'text': self.text,
            'orig_text': self.orig_text,
            'user': self.user.to_dict(),
            'annotations': self.annotations,
            'date_time': str(self.date_time)
        }


class Dialog(DynamicDocument):
    location = DynamicField()
    utterances = ListField(ReferenceField(Utterance), default=[])
    channel_type = StringField(choices=['telegram', 'vk', 'facebook', 'cmd_client', 'http_client'], default='telegram')
    version = StringField(default=STATE_API_VERSION, required=True)
    human_id = ObjectIdField(required=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'location': self.location,
            'utterances': [utt.to_dict() for utt in self.utterances],
            'channel_type': self.channel_type,
            'human_id': self.human_id
        }

