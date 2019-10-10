# -*- coding: utf-8 -*-
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
import ask_sdk_core.utils as ask_utils
import requests
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import \
    AwsLambdaIntegration


SENTRY_DSN = 'https://7a6d57df6fb44ae4bfc3d43a8b4f16f3@sentry.io/1553895'
DP_AGENT_URL = 'http://Docker-ExternalLoa-LOFSURITNPLE-525614984.us-east-1.elb.amazonaws.com:4242'

sentry_sdk.init(
    SENTRY_DSN,
    integrations=[AwsLambdaIntegration()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

request_data = None


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hi, this is an Alexa Prize Socialbot. How are you?"

        return (
            handler_input.response_builder.speak(speak_output).ask(speak_output).response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello Python World from Classes!"

        return (
            handler_input.response_builder.speak(speak_output).ask(speak_output).response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder.speak(speak_output).ask(speak_output).response
        )


class StopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("StopIntentHandler")
        # type: (HandlerInput) -> Response
        speak_output = ""

        return (
            handler_input.response_builder.speak(speak_output).response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("SessionEndedRequestHandler")
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


def call_dp_agent(user_id, text):
    logger.info("call_dp_agent user_id: {}; text: {}".format(user_id, text))
    response, intent = None, None
    r = requests.post(DP_AGENT_URL, json={'user_id': user_id, 'payload': text}).json()
    if r['active_skill'] == 'intent_responder':
        response, intent = r["response"].split("#+#")
    else:
        response = r["response"]

    return {'response': response, 'intent': intent}


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        user_id = ask_utils.get_user_id(handler_input)
        text = ask_utils.get_slot_value(handler_input, 'navigation')
        if not text:
            # try to take the most probable hypothesis
            if 'speechRecognition' in request_data['request']:
                speech = request_data['request']['speechRecognition']
                speech_text = ' '.join([token['value'] for token in speech['hypotheses'][0]['tokens']])
                logger.info(f'got text from speech: {speech_text}')
                dp_agent_data = call_dp_agent(user_id, speech_text)
            else:
                dp_agent_data = {"response": "Sorry", "intent": None}
                logger.warning("NO TEXT NO SPEECH!")
                sentry_sdk.capture_message("no text! no speech!")
        else:
            dp_agent_data = call_dp_agent(user_id, text)
        speak_output = dp_agent_data['response']

        if dp_agent_data['intent'] == 'exit':
            logger.info("ExitIntent From DpAgent")
            return handler_input.response_builder.speak(speak_output).response
        else:
            logger.info("Normal output from DpAgent")
            return handler_input.response_builder.speak(speak_output).ask(speak_output).response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        sentry_sdk.capture_exception(exception)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder.speak(speak_output).ask(speak_output).response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(StopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()


def handler_wrapper(event, context):
    global request_data
    request_data = event
    return handler(event=event, context=context)
