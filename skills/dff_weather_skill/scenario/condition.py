from df_engine.core import Actor, Context

from common.dff.integration.context import get_last_bot_utterance, get_last_human_utterance
from common.utils import get_intents
from common.universal_templates import if_chat_about_particular_topic
from common.weather import WEATHER_COMPILED_PATTERN, WEATHER_REQUEST_COMPILED_PATTERN, is_weather_for_homeland_requested
from scenario.utils import retrieve_location_entity_from_utterance


def request_with_location_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utter = get_last_human_utterance(ctx, actor)
    location_name = retrieve_location_entity_from_utterance(human_utter)
    return bool(location_name)


def forecast_requested_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    is_forecast_requested = WEATHER_REQUEST_COMPILED_PATTERN.search(ctx.last_request)
    return bool(is_forecast_requested)


def forecast_intent_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utter = get_last_human_utterance(ctx, actor)
    is_forecast_intent = "weather_forecast_intent" in get_intents(human_utter, probs=False, which="intent_catcher")
    return bool(is_forecast_intent)


def chat_about_weather_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utter = get_last_human_utterance(ctx, actor)
    bot_utter = get_last_bot_utterance(ctx, actor)
    return bool(if_chat_about_particular_topic(human_utter, bot_utter, compiled_pattern=WEATHER_COMPILED_PATTERN))


def homeland_forecast_requested_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utter = get_last_human_utterance(ctx, actor)
    bot_utter = get_last_bot_utterance(ctx, actor)
    return bool(is_weather_for_homeland_requested(bot_utter, human_utter))
