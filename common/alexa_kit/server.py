from os import getenv

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response
from flask import Flask
from flask_ask_sdk.skill_adapter import SkillAdapter
import requests

app = Flask(__name__)
skill_builder = SkillBuilder()

ALEXA_SKILL_ID = getenv("ALEXA_SKILL_ID")
AGENT_URL = getenv("AGENT_URL")


def post_to_agent(user_id: str, text: str) -> str:
    payload = {
        "user_id": user_id,
        "payload": text
    }
    response = requests.post(AGENT_URL, json=payload)
    response_text = response.json()["response"]

    return response_text


class LaunchRequestHandler(AbstractRequestHandler):

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = "This is Dream! Let's talk!"

        handler_input.response_builder.speak(speech_text).ask(
            "Go ahead and say anything to me!").set_card(
            SimpleCard("Hello World", speech_text))
        return handler_input.response_builder.response


class ChatHandler(AbstractRequestHandler):

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("ChatWithDream")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        request_dict = handler_input.request_envelope.request.to_dict()
        # user_id = handler_input.request_envelope.session.user.user_id
        user_id = handler_input.request_envelope.session.session_id
        text = request_dict["intent"]["slots"]["raw_input"]["value"]

        speech_text = post_to_agent(user_id, text)

        handler_input.response_builder.speak(speech_text).ask(
            "Go ahead and say anything to me!").set_card(
            SimpleCard("Dream Chat", speech_text))
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = "Just say anything to me and we'll have a chat!"
        handler_input.response_builder.speak(speech_text).ask(
            "Go ahead and say anything to me!").set_card(
            SimpleCard("Dream Chat", speech_text))
        return handler_input.response_builder.response


class CancelAndStopIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input: HandlerInput) -> bool:
        is_cancel = is_intent_name("AMAZON.CancelIntent")(handler_input)
        is_stop = is_intent_name("AMAZON.StopIntent")(handler_input)
        return is_cancel or is_stop

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = "Bye!"
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Dream Chat", speech_text))
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = "Thanks for the chat session, bye!"
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Dream Chat", speech_text))
        return handler_input.response_builder.response


skill_builder.add_request_handler(LaunchRequestHandler())
skill_builder.add_request_handler(ChatHandler())
skill_builder.add_request_handler(HelpIntentHandler())
skill_builder.add_request_handler(CancelAndStopIntentHandler())
skill_builder.add_request_handler(SessionEndedRequestHandler())
# skill_builder.add_request_handler(FallbackIntentHandler())

skill_adapter = SkillAdapter(
    skill=skill_builder.create(), skill_id=ALEXA_SKILL_ID, app=app)


@app.route("/", methods=["POST"])
def invoke_skill():
    """Can be used by Alexa only"""
    return skill_adapter.dispatch_request()
