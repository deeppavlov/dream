import asyncio
from collections import defaultdict
from time import time
from typing import Any, Callable, Hashable, Optional

from core.pipeline import Pipeline
from core.state_manager import StateManager
from core.state_schema import Dialog

import logging
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, pipeline: Pipeline, state_manager: StateManager,
                 process_logger_callable: Optional[Callable] = None,
                 response_logger_callable: Optional[Callable] = None):
        self.workflow = dict()
        self.pipeline = pipeline
        self.state_manager = state_manager
        self.process_logger_callable = process_logger_callable
        self.response_logger_callable = response_logger_callable

    def add_workflow_record(self, dialog: Dialog, deadline_timestamp: Optional[float] = None, **kwargs):
        if str(dialog.id) in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog.id} is already in workflow')
        workflow_record = {'dialog': dialog, 'services': defaultdict(dict)}
        if deadline_timestamp:
            workflow_record['deadline_timestamp'] = deadline_timestamp
        if 'dialog_object' in kwargs:
            raise ValueError("'dialog_object' is system reserved workflow record field")
        workflow_record.update(kwargs)
        self.workflow[str(dialog.id)] = workflow_record

    def get_workflow_record(self, dialog_id):
        record = self.workflow.get(dialog_id, None)
        if not record:
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        return record

    def flush_record(self, dialog_id: str):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        if self.response_logger_callable:
            self.response_logger_callable(self.workflow[dialog_id])
        return self.workflow.pop(dialog_id)

    def register_service_request(self, dialog_id: str, service_name):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        self.workflow[dialog_id]['services'][service_name] = {'send': True, 'done': False, 'agent_send_time': time(),
                                                              'agent_done_time': None}

    def get_services_status(self, dialog_id: str):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        done, waiting = set(), set()
        for key, value in self.workflow[dialog_id]['services'].items():
            if value['done']:
                done.add(key)
            else:
                waiting.add(key)

        return done, waiting

    async def process_service_response(self, dialog_id: str, service_name: str = None, response: Any = None,
                                       **kwargs):
        if "dialog_object" not in response:
            logger.info(f"Service: {response}")
        workflow_record = self.get_workflow_record(dialog_id)

        # Updating workflow with service response
        service = self.pipeline.get_service_by_name(service_name)
        if service:
            service_data = self.workflow[dialog_id]['services'][service_name]
            service_data['done'] = True
            service_data['agent_done_time'] = time()
            if service.state_processor_method:
                await service.state_processor_method(
                    dialog=workflow_record['dialog'], payload=response,
                    message_attrs=kwargs.pop('message_attrs', {})
                )

            # passing kwargs to services record
            if not set(service_data.keys()).intersection(set(kwargs.keys())):
                service_data.update(kwargs)

        # Flush record  and return zero next services if service is is_responder
        if service.is_responder():
            if not workflow_record.get('hold_flush'):
                self.flush_record(dialog_id)
            return []

        # Calculating next steps
        done, waiting = self.get_services_status(dialog_id)
        next_services = self.pipeline.get_next_services(done, waiting)

        # Processing the case, when service is a skill selector
        if service and service.is_sselector():
            selected_services = list(response.values())[0]
            result = []
            for service in next_services:
                if service.name not in selected_services:
                    self.workflow[dialog_id]['services'][service.name] = {'done': True, 'send': False,
                                                                          'agent_send_time': None,
                                                                          'agent_done_time': None}
                else:
                    result.append(service)
            next_services = result
        # send dialog workflow record to further logging operations:
        if self.process_logger_callable:
            self.process_logger_callable(self.workflow['dialog_id'])

        return next_services

    async def register_msg(self, utterance: str, user_telegram_id: Hashable,
                           user_device_type: Any, location: Any,
                           channel_type: str, deadline_timestamp=None,
                           require_response=False, **kwargs):
        dialog = await self.state_manager.get_or_create_dialog_by_tg_id(user_telegram_id, channel_type)
        dialog_id = str(dialog.id)
        service_name = 'input'
        message_attrs = kwargs.pop('message_attrs', {})

        if require_response:
            event = asyncio.Event()
            kwargs['event'] = event
            self.add_workflow_record(dialog=dialog, deadline_timestamp=deadline_timestamp, hold_flush=True, **kwargs)
            self.register_service_request(dialog_id, service_name)
            await self.process(dialog_id, service_name, response=utterance, message_attrs=message_attrs)
            await event.wait()
            return self.flush_record(dialog_id)

        self.add_workflow_record(dialog=dialog, deadline_timestamp=deadline_timestamp, **kwargs)
        self.register_service_request(dialog_id, service_name)
        await self.process(dialog_id, service_name, response=utterance, message_attrs=message_attrs)

    async def process(self, dialog_id, service_name=None, response: Any = None, **kwargs):
        workflow_record = self.get_workflow_record(dialog_id)
        next_services = await self.process_service_response(dialog_id, service_name, response, **kwargs)

        service_requests = []
        for service in next_services:
            self.register_service_request(dialog_id, service.name)
            payload = service.apply_workflow_formatter(workflow_record)
            service_requests.append(
                service.connector_func(payload=payload, callback=self.process)
            )

        await asyncio.gather(*service_requests)
