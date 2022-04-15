from fastapi import FastAPI
from pydantic import BaseModel, BaseSettings
import requests


class APISettings(BaseSettings):
    agent_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


class AliceMetaData(BaseModel):
    locale: str
    timezone: str
    client_id: str
    interfaces: dict


class AliceSessionData(BaseModel):
    message_id: int
    session_id: str
    skill_id: str
    user: dict
    application: dict
    new: bool
    user_id: str


class AliceRequestData(BaseModel):
    command: str
    original_utterance: str
    nlu: dict
    markup: dict
    type: str


class AliceRequest(BaseModel):
    """Must conform with https://yandex.ru/dev/dialogs/alice/doc/request.html
    """
    meta: AliceMetaData
    request: AliceRequestData
    session: AliceSessionData
    state: dict = {}
    version: str


class AliceResponseData(BaseModel):
    text: str
    tts: str = ""
    # card: dict = {}
    # buttons: list = []
    end_session: bool = False
    # directives: dict = {}


class AliceResponse(BaseModel):
    """Must conform with https://yandex.ru/dev/dialogs/alice/doc/response.html
    """
    response: AliceResponseData
    session_state: dict = {}
    user_state_update: dict = {}
    application_state: dict = {}
    analytics: dict = {}
    version: str = "1.0"

    @classmethod
    def from_text(cls, text: str, tts: str = ""):
        """Helper classmethod for instantiating Alice response with text and text-to-speech,
        setting other fields to their default values

        Args:
            text: response text
            tts: response text-to-speech in yandex format,
                see https://yandex.ru/dev/dialogs/alice/doc/speech-tuning.html

        Returns:

        """
        return cls(response=AliceResponseData(text=text, tts=tts))


settings = APISettings()
app = FastAPI()


def post_to_agent(user_id: str, text: str) -> str:
    payload = {
        "user_id": user_id,
        "payload": text
    }
    response = requests.post(settings.agent_url, json=payload)
    response_text = response.json()["response"]

    return response_text


@app.post("/")
def invoke_skill(alice_request: AliceRequest):
    """Alice webhook endpoint.
    According to https://yandex.ru/dev/dialogs/alice/doc/publish-settings.html,
    response time must be < 3 seconds or Alice will tell the user that the skill is not responding
    """
    user_id = alice_request.session.session_id
    user_text = alice_request.request.original_utterance

    text = tts = post_to_agent(user_id, user_text)

    return AliceResponse.from_text(text=text, tts=tts)
