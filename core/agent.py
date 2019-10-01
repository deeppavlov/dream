import asyncio

from collections import defaultdict
from time import time
from typing import Any, Optional, Callable, Hashable

from core.pipeline import Pipeline
from core.state_manager import StateManager
from core.state_schema import Dialog
from models.hardcode_utterances import TG_START_UTT


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
        workflow_record = {'dialog_object': dialog, 'dialog': dialog.to_dict(), 'services': defaultdict(dict)}
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
        self.workflow[dialog_id]['services'][service_name] = {'send': True, 'done': False, 'send_time': time(),
                                                              'done_time': None}

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

    def process_service_response(self, dialog_id: str, service_name: str = None, response: Any = None,
                                 response_time: float = None):
        workflow_record = self.get_workflow_record(dialog_id)

        # Updating workflow with service response
        service = self.pipeline.get_service_by_name(service_name)
        if service:
            service_data = self.workflow[dialog_id]['services'][service_name]
            service_data['done'] = True
            service_data['done_time'] = response_time
            if response and service.state_processor_method:
                service.state_processor_method(dialog=workflow_record['dialog'],
                                               dialog_object=workflow_record['dialog_object'],
                                               payload=response)
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
                                                                          'send_time': None, 'done_time': None}
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
        user = self.state_manager.get_or_create_user(user_telegram_id, user_device_type)
        should_reset = True if utterance == TG_START_UTT else False
        dialog = self.state_manager.get_or_create_dialog(user, location, channel_type, should_reset=should_reset)
        if require_response:
            event = asyncio.Event()
            kwargs['event'] = event
            self.add_workflow_record(dialog=dialog, deadline_timestamp=deadline_timestamp, hold_flush=True, **kwargs)
            self.register_service_request(str(dialog.id), 'input')
            await self.process(str(dialog.id), 'input', utterance, time())
            await event.wait()
            return self.flush_record(str(dialog.id))

        else:
            self.add_workflow_record(dialog=dialog, deadline_timestamp=deadline_timestamp, **kwargs)
            self.register_service_request(str(dialog.id), 'input')
            await self.process(str(dialog.id), 'input', utterance, time())

    async def process(self, dialog_id, service_name=None, response: Any = None, response_time: float = None):
        workflow_record = self.get_workflow_record(dialog_id)
        next_services = self.process_service_response(dialog_id, service_name, response, response_time)

        service_requests = []
        for service in next_services:
            self.register_service_request(dialog_id, service.name)
            payload = service.apply_workflow_formatter(workflow_record)
            service_requests.append(
                service.connector_func(payload=payload, callback=self.process)
            )

        await asyncio.gather(*service_requests)
