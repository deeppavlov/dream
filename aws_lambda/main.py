# -*- coding: utf-8 -*-
import logging
import os

import ask_sdk_core.utils as ask_utils
import requests
import sentry_sdk
import json
import hashlib
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model import Response
from dotenv import load_dotenv
from sentry_sdk.integrations.aws_lambda import \
    AwsLambdaIntegration

load_dotenv()

SENTRY_DSN = os.getenv('SENTRY_DSN')
DP_AGENT_URL = os.getenv('DP_AGENT_URL')
DP_AGENT_PORT = os.getenv('DP_AGENT_PORT')

A_VERSION = os.getenv('A_VERSION')
A_AGENT_URL = os.getenv('A_AGENT_URL')
A_AGENT_PORT = os.getenv('A_AGENT_PORT')
B_VERSION = os.getenv('B_VERSION')
B_AGENT_URL = os.getenv('B_AGENT_URL')
B_AGENT_PORT = os.getenv('B_AGENT_PORT')

ab_tests_mode = False
if A_AGENT_URL is not None and B_AGENT_URL is not None and A_AGENT_PORT != B_AGENT_PORT:
    ab_tests_mode = True

sentry_sdk.init(
    SENTRY_DSN,
    integrations=[AwsLambdaIntegration()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info(f"running in A/B tests mode: {ab_tests_mode}")

request_data = None


def get_conversation_id(request_data):
    request_section = request_data['request']
    conversation_id = request_section.get('conversation_id') or request_data.get('conversation_id')
    conversation_id = conversation_id or request_section.get('conversationId') or request_data.get('conversationId')

    if not conversation_id:
        if 'payload' in request_section:
            payload = request_section['payload']
            conversation_id = payload.get('conversationId') or payload.get('conversaion_id')
    return conversation_id


def call_dp_agent(user_id, text, request_data):
    device_id, session_id, request_id = "", "", ""
    try:
        device_id = request_data['context']['System']['device'].get('deviceId')
        session_id = request_data['session']['sessionId']
        request_id = request_data['request']['requestId']
    except KeyError as e:
        logger.error("No key in request_data")
        sentry_sdk.capture_exception(e)

    speech = []
    try:
        speech = request_data['request']['speechRecognition']
    except KeyError:
        speech = request_data['request'].get('payload', {}).get('speechRecognition', [])
        if not speech:
            logger.error("No speech in request_data")

    conversation_id = get_conversation_id(request_data)

    response, intent = None, None
    dp_agent_url = f'{DP_AGENT_URL}:{DP_AGENT_PORT}'

    # A/B tests logic
    # currently if A/B tests are not runing version is set to None
    version = None
    if ab_tests_mode:
        if hashlib.md5(user_id.encode()).digest()[-1] % 2 == 0:
            dp_agent_url = f'{A_AGENT_URL}:{A_AGENT_PORT}'
            version = A_VERSION
        else:
            dp_agent_url = f'{B_AGENT_URL}:{B_AGENT_PORT}'
            version = B_VERSION
        logger.info(f"User {user_id}\n sent to version {version} on {dp_agent_url}")
    try:
        r = requests.post(
            dp_agent_url,
            json={'user_id': user_id, 'payload': text, 'device_id': device_id,
                  'session_id': session_id, 'request_id': request_id,
                  'conversation_id': conversation_id, 'speech': speech, 'version': version},
            timeout=5.5).json()
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        sentry_sdk.capture_exception(e)
        logger.exception("AWS_LAMBDA Timeout")
        return {'response': "I am thinking...", 'intent': None}
    except json.JSONDecodeError as e:
        sentry_sdk.capture_exception(e)
        logger.exception("AWS_LAMBDA JSONDecodeError")
        return {
            'response': "We'll meet again, Don't know where, don't know when,"
                        "But I know we'll meet again, Some sunny day.",
            'intent': 'exit'}

    if r.get('active_skill') == 'intent_responder' or '#+#' in r["response"]:
        response, intent = r["response"].split("#+#")
        if intent[-1] == '.':  # Programy dangerous returns with . in the end
            intent = intent[:-1]
    else:
        response = r["response"]

    logger.info("call_dp_agent user_id: {}; text: {}; repsonse: {}; intent: {}".format(
        user_id, text, response, intent
    ))
    return {'response': response, 'intent': intent}
    # Disable voice effect v8.7.0
    # if r.get("ssml_tagged_response"):
    #     return {'response': response, 'ssml_tagged_response': r["ssml_tagged_response"], 'intent': intent}
    # else:


def process_dp_agent_response(agent_data, user_id, handler_input):
    speak_output = agent_data['response']
    if agent_data['intent'] == 'exit':
        call_dp_agent(user_id, '/close', request_data)
        logger.info("ExitIntent From DpAgent")
        return handler_input.response_builder.speak(speak_output).response
    else:
        logger.info(f"Normal output from DpAgent: {speak_output}")
        # TODO: Think how to validate invalid SSML responses!!!
        if "ssml_tagged_response" in agent_data:
            # Voice effects disabled in v8.7.0 call_dp_agent function so it never be called
            speak_output = agent_data["ssml_tagged_response"]
        else:
            speak_output = speak_output.replace(">", " ").replace("<", " ").replace("&", " and ")
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response


def get_text_from_speech(speech):
    tokens, probs = zip(*[(token['value'], token['confidence']) for token in speech['hypotheses'][0]['tokens']])
    text = ' '.join(tokens)
    logger.info(f'got text from speech: {text}')
    mean_proba = sum(probs) / len(probs)
    return text, mean_proba


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # speak_output = "Hi, this is an Alexa Prize Socialbot. How are you?"
        user_id = ask_utils.get_user_id(handler_input)
        call_dp_agent(user_id, '/start', request_data)
        # text = "Alexa, let's chat."
        speech = request_data['request'].get('payload', {}).get('speechRecognition', None)
        # sometimes LaunchRequest comes with no tokens in speechRecognition
        if speech is not None and len(speech['hypotheses'][0]['tokens']) > 0:
            text, _ = get_text_from_speech(speech)
        else:
            text = "hello"
        logger.info(f'LaunchRequestHandler send text to dp_agent: {text}')
        dp_agent_data = call_dp_agent(user_id, text, request_data)
        return process_dp_agent_response(dp_agent_data, user_id, handler_input)


class StopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("StopIntentHandler")
        # type: (HandlerInput) -> Response
        speak_output = ""
        user_id = ask_utils.get_user_id(handler_input)
        call_dp_agent(user_id, '/alexa_stop_handler', request_data)
        call_dp_agent(user_id, '/close', request_data)
        return (
            handler_input.response_builder.speak(speak_output).set_should_end_session(True).response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        user_id = ask_utils.get_user_id(handler_input)
        r = request_data['request']
        # reason can be one of: ERROR, EXCEEDED_MAX_REPROMPTS, USER_INITIATED
        if r.get('reason') == 'ERROR':
            with sentry_sdk.push_scope() as scope:
                scope.set_extra('request_data', request_data)
                sentry_sdk.capture_message('ERROR in SessionEndedRequestHandler!!!')
            call_dp_agent(user_id, '/alexa_error_in_session_ending', request_data)
        elif r.get('reason') == 'EXCEEDED_MAX_REPROMPTS':
            call_dp_agent(user_id, '/alexa_exceeded_max_reprompts', request_data)
        else:
            call_dp_agent(user_id, f"/alexa_{r.get('reason', 'SessionEndedRequest')}", request_data)
        # Any cleanup logic goes here.
        return handler_input.response_builder.response


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
        slot_text = ask_utils.get_slot_value(handler_input, 'navigation')

        # try to take the most probable hypothesis
        if 'speechRecognition' in request_data['request']:
            speech = request_data['request']['speechRecognition']
            speech_text, _ = get_text_from_speech(speech)
            dp_agent_data = call_dp_agent(user_id, speech_text, request_data)
        elif slot_text is not None and len(slot_text) > 0:
            # in case if there is no speech in request, get slot value
            dp_agent_data = call_dp_agent(user_id, slot_text, request_data)
        elif ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input):
            text = 'cancel'
            logger.info(f'got AMAZON.CancelIntent, set text to: {text}')
            dp_agent_data = call_dp_agent(user_id, text, request_data)
        elif ask_utils.is_intent_name("ByeIntent")(handler_input):
            # todo: remove from Intent Schema redundant intents
            text = 'bye'
            logger.info(f'got ByeIntent, set text to: {text}')
            dp_agent_data = call_dp_agent(user_id, text, request_data)
        else:
            dp_agent_data = {"response": "Sorry", "intent": None}
            msg = f"LAMBDA: NO TEXT NO SPEECH! incoming request: {request_data['request']}"
            logger.warning(msg)
            sentry_sdk.capture_message(msg)

        return process_dp_agent_response(dp_agent_data, user_id, handler_input)


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
sb.add_request_handler(StopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()


def handler_wrapper(event, context):
    global request_data
    request_data = event
    if 'request' in request_data:
        logger.info(f'incoming request: {request_data["request"]}')
    else:
        msg = 'LAMBDA: no field request in request_data'
        logger.warning(msg)
        sentry_sdk.capture_message(msg)

    return handler(event=event, context=context)
