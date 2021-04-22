import logging
from importlib import import_module
from typing import Dict

from .core.db import DataBase
from .core.state_manager import StateManager, Dialog
from .core.workflow_manager import WorkflowManager
from .state_formatters.output_formatters import http_api_output_formatter, http_debug_output_formatter


# Default parameters
BASE_PARAMETERS = {
    "debug": True,
    "state_manager_class": StateManager,
    "workflow_manager_class": WorkflowManager,
    "db_class": DataBase,
    "pipeline_config": "pipeline_conf.json",
    "db_config": "db_conf.json",
    "overwrite_last_chance": None,
    "overwrite_timeout": None,
    "formatters_module": None,
    "connectors_module": None,
    "response_logger": True,
    "time_limit": 0,
    "output_formatter": http_api_output_formatter,
    "debug_output_formatter": http_debug_output_formatter,
    "port": 4242,
    "cors": False,
    "telegram_token": "",
    "telegram_proxy": "",
}


# Replasing constants with ones from user settings
def setup_parameter(name, user_settings):
    res = None
    if user_settings:
        res = getattr(user_settings, name, None)
    if res is None:
        res = BASE_PARAMETERS[name]
    return res


user_settings = None
try:
    user_settings = import_module("dp_agent_settings")
except ModuleNotFoundError:
    logging.info("settings.py was not found. Default settings are used")

# Set up common parameters
DEBUG = setup_parameter("debug", user_settings)


class ExtendedStateManager(StateManager):
    async def update_attributes(self, dialog, payload, label: str, **kwargs):
        if isinstance(payload.get("human_attributes"), dict):
            await self.update_human(dialog.human, payload)
        if isinstance(payload.get("bot_attributes"), dict):
            await self.update_bot(dialog.bot, payload)

    async def add_annotation_and_reset_human_attributes_for_first_turn(
        self, dialog: Dialog, payload: Dict, label: str, **kwargs
    ):
        dialog.utterances[-1].annotations[label] = payload
        if len(dialog.utterances) == 1:
            dialog.human.attributes = {"disliked_skills": dialog.human.attributes.get("disliked_skills", [])}


# Basic agent configuration parameters (some are currently unavailable)
STATE_MANAGER_CLASS = ExtendedStateManager
WORKFLOW_MANAGER_CLASS = WorkflowManager
DB_CLASS = DataBase

PIPELINE_CONFIG = setup_parameter("pipeline_config", user_settings)
DB_CONFIG = setup_parameter("db_config", user_settings)

OVERWRITE_LAST_CHANCE = setup_parameter("overwrite_last_chance", user_settings)
OVERWRITE_TIMEOUT = setup_parameter("overwrite_timeout", user_settings)

RESPONSE_LOGGER = setup_parameter("response_logger", user_settings)

# HTTP app configuraion parameters
TIME_LIMIT = setup_parameter("time_limit", user_settings)  # Without engaging the timeout by default
CORS = setup_parameter("cors", user_settings)

OUTPUT_FORMATTER = setup_parameter("output_formatter", user_settings)
DEBUG_OUTPUT_FORMATTER = setup_parameter("debug_output_formatter", user_settings)

# HTTP api run parameters
PORT = setup_parameter("port", user_settings)

# Telegram client configuration parameters
TELEGRAM_TOKEN = setup_parameter("telegram_token", user_settings)
TELEGRAM_PROXY = setup_parameter("telegram_proxy", user_settings)
