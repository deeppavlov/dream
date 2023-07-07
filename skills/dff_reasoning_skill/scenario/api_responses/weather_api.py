from os import getenv
import json
from tools.city_slot import OWMCitySlot
from tools.weather_service import weather_forecast_now
from df_engine.core import Context, Actor
from scenario.utils import compose_input_for_API

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}

API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)

for key, value in api_conf.copy().items():
    for api_key in value["keys"]:
        if not available_variables[api_key]:
            del api_conf[key]
            break

if "weather_api" in api_conf.keys():
    CITY_SLOT = OWMCitySlot()


def weather_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    api_input = compose_input_for_API(ctx, actor)
    location_name = CITY_SLOT(api_input)
    return weather_forecast_now(location_name)
