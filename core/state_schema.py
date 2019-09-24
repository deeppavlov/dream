from mongoengine import DynamicDocument, ReferenceField, ListField, StringField, DynamicField, DateTimeField,\
    FloatField, DictField

from . import STATE_API_VERSION

HUMAN_UTTERANCE_SCHEMA = {
    'id': None,
    'text': None,
    'user': {},
    'annotations': {},
    'date_time': None,
    'selected_skills': {},
    'type': 'human'
}

BOT_UTTERANCE_SCHEMA = {
    'id': None,
    'active_skill': None,
    'confidence': None,
    'text': None,
    'orig_text': None,
    'user': {},
    'annotations': {},
    'date_time': None,
    'type': 'bot'
}

BOT_SCHEMA = {
    'id': None,
    'persona': [],
    'attributes': {}
}

HUMAN_SCHEMA = {
    'id': None,
    'user_telegram_id': None,
    'device_type': None,
    'persona': [],
    'profile': {
        "name": None,
        "gender": None,
        "birthdate": None,
        "location": None,
        "home_coordinates": None,
        "work_coordinates": None,
        "occupation": None,
        "income_per_year": None
    },
    'attributes': {}
}

DIALOG_SCHEMA = {
    'id': [],
    'location': [],
    'utterances': [],
    'channel_type': None,
    'human': None,
    'bot': None
}


class User(DynamicDocument):
    persona = ListField(default=[])
    attributes = DictField()

    meta = {'allow_inheritance': True}

    def to_dict(self):
        raise NotImplementedError

    def update_from_dict(self, *args, **kwargs):
        raise NotImplementedError


class Bot(User):

    def to_dict(self):
        return {'id': str(self.id),
                'user_type': 'bot',
                'persona': self.persona,
                'attributes': self.attributes
                }

    def update_from_dict(self, payload):
        self.persona = payload['persona']
        self.attributes = payload['attributes']


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
        "income_per_year": None,
    })

    def to_dict(self):
        return {'id': str(self.id),
                'user_telegram_id': str(self.user_telegram_id),
                'user_type': 'human',
                'device_type': self.device_type,
                'persona': self.persona,
                'profile': self.profile,
                'attributes': self.attributes
                }

    def update_from_dict(self, payload):
        self.device_type = payload['device_type']
        self.persona = payload['persona']
        self.profile = payload['profile']
        self.attributes = payload['attributes']


class Utterance(DynamicDocument):
    text = StringField(required=True)
    annotations = DictField(default={})
    user = DictField(default={})
    date_time = DateTimeField(required=True)

    meta = {'allow_inheritance': True}

    def to_dict(self):
        raise NotImplementedError

    def make_from_dict(self, *args, **kwargs):
        raise NotImplementedError


class HumanUtterance(Utterance):
    selected_skills = DynamicField(default=[])

    def to_dict(self):
        return {
            'id': str(self.id),
            'text': self.text,
            'user': self.user,
            'annotations': self.annotations,
            'date_time': str(self.date_time),
            'selected_skills': self.selected_skills,
            'type': 'human'
        }

    @classmethod
    def make_from_dict(cls, payload):
        utterance = cls()
        utterance.id = payload['id']
        utterance.text = payload['text']
        utterance.annotations = payload['annotations']
        utterance.date_time = payload['date_time']
        utterance.selected_skills = payload['selected_skills']
        utterance.user = payload['user']
        utterance.save()
        return utterance


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
            'user': self.user,
            'annotations': self.annotations,
            'date_time': str(self.date_time),
            'type': 'bot'
        }

    @classmethod
    def make_from_dict(cls, payload):
        utterance = cls()
        utterance.id = payload['id']
        utterance.text = payload['text']
        utterance.orig_text = payload['orig_text']
        utterance.annotations = payload['annotations']
        utterance.date_time = payload['date_time']
        utterance.active_skill = payload['active_skill']
        utterance.confidence = payload['confidence']
        utterance.user = payload['user']
        utterance.save()
        return utterance


class Dialog(DynamicDocument):
    location = DynamicField()
    utterances = ListField(ReferenceField(Utterance), default=[])
    channel_type = StringField(choices=['telegram', 'vk', 'facebook', 'cmd_client', 'http_client'], default='telegram')
    version = StringField(default=STATE_API_VERSION, required=True)
    human = ReferenceField(Human, required=True)
    bot = ReferenceField(Bot, required=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'location': self.location,
            'utterances': [utt.to_dict() for utt in self.utterances],
            'channel_type': self.channel_type,
            'human': self.human.to_dict(),
            'bot': self.bot.to_dict()
        }

    @classmethod
    def make_from_dict(cls, payload):
        dialog = cls()
        dialog.location = payload['location']
        dialog.channel_type = payload['channel_type']
        return dialog
