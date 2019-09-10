import asyncio

from collections import defaultdict
from datetime import datetime
from time import time
from typing import Any, Optional, Callable, Hashable

from core.pipeline import Pipeline
from core.state_manager import StateManager
from core.state_schema import Dialog


class AsyncAgent:
    def __init__(self, pipeline: Pipeline, state_manager: StateManager,
                 process_logger_callable: Optional[Callable] = None,
                 response_logger_callable: Optional[Callable] = None):
        self.workflow = dict()
        self.pipeline = pipeline
        self.state_manager = state_manager
        self.process_logger_callable = process_logger_callable
        self.response_logger_callable = response_logger_callable

    def add_workflow_record(self, dialog: Dialog, deadline_timestamp: Optional[float] = None, **kwargs):
        if dialog.id in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog.id} is already in workflow')
        workflow_record = {'dialog': dialog, 'services': defaultdict(dict)}
        if deadline_timestamp:
            workflow_record['deadline_timestamp'] = deadline_timestamp
        if 'dialog' in kwargs:
            raise ValueError("'dialog' key is system reserved")
        if 'services' in kwargs:
            raise ValueError("'services key' is system reserved")
        if 'deadline_timestamp' in kwargs:
            raise ValueError("'deadline_timestamp' key is system reserved")
        workflow_record.update(kwargs)
        self.workflow[dialog.id] = workflow_record

    def get_workflow_record(self, dialog_id):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        return self.workflow[dialog_id]

    def flush_record(self, dialog_id: str):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        return self.workflow.pop(dialog_id)

    def register_service_request(self, dialog_id: str, service_name):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        self.workflow[dialog_id]['services'][service_name] = {'send': time(), 'done': None}

    def get_services_status(self, dialog_id: str):
        if dialog_id not in self.workflow.keys():
            raise ValueError(f'dialog with id {dialog_id} is not exist in workflow')
        done, waiting = set(), set()
        for key, value in self.workflow[dialog_id]['services'].items():
            if value['done'] is not None:
                done.add(key)
            else:
                waiting.add(key)

        return done, waiting

    def process_service_response(self, dialog_id: str, service_name: str = None, response: str = None):
        '''
        Ultimate method, which performs next operations:
        1. Updates workflow dict with completed service
        2. Updates dialog within workflow dict, using service update callable
        3. Asks pipeline for next services which became available on current stage workflow
        4. Modifies next services when processed responce is received from a selector service
        5. Returns next services in list form
        '''
        workflow_record = self.get_workflow_record(dialog_id)

        # Updating workflow with service response
        service = self.pipeline.get_service_by_name(service_name)
        if service:
            self.workflow[dialog_id]['services'][service_name]['done'] = time()
            if response:
                service.state_processor_method(workflow_record['dialog'], response)

        # Calculating next steps
        done, waiting = self.get_services_status(dialog_id)
        next_services = self.pipeline.get_next_services(done, waiting)

        # Processing the case, when service is skill selector
        if service and service.is_selector():
            selected_services = list(response.values())[0]
            result = []
            for service in next_services:
                if service.name not in selected_services:
                    self.workflow[dialog_id]['services'][service.name] = {'done': time(), 'send': None}
                else:
                    result.append(service)
            next_services = result
        if self.process_logger_callable:
            self.process_logger_callable(self.workflow['dialog_id'])  # send dialog workflow record to further logging operations

        return next_services

    async def register_msg(self, utterance: str, user_telegram_id: Hashable,
                           user_device_type: Any,
                           date_time: datetime, location=Any,
                           channel_type=str, deadline_timestamp=None, **kwargs):

        user = self.state_manager.get_or_create_user(user_telegram_id, user_device_type)
        dialog = self.state_manager.get_or_create_dialog(user, location, channel_type)
        self.state_manager.add_human_utterance(dialog, utterance, date_time)
        self.add_workflow_record(dialog, deadline_timestamp, **kwargs)

        await self.process(dialog.id)

    async def process(self, dialog_id, service_name=None, response=None):
        workflow_record = self.get_workflow_record(dialog_id)
        next_services = self.process_service_response(dialog_id, service_name, response)

        for service in next_services:
            self.register_service_request(dialog_id, service.name)
            payload = service.apply_workflow_formatter(workflow_record)
            response = await service.connector.send(payload)
            if service.is_responder():
                self.flush_record(dialog_id)
                break
            if response is not None:
                await self.process(dialog_id, service.name, response)
