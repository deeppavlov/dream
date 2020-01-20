import asyncio
from typing import Any, Hashable

from core.log import BaseResponseLogger
from core.pipeline import Pipeline
from core.state_manager import StateManager
from core.workflow_manager import WorkflowManager

import logging
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent:
    _response_logger: BaseResponseLogger

    def __init__(self,
                 pipeline: Pipeline,
                 state_manager: StateManager,
                 workflow_manager: WorkflowManager,
                 response_logger: BaseResponseLogger) -> None:
        self.pipeline = pipeline
        self.state_manager = state_manager
        self.workflow_manager = workflow_manager
        self._response_logger = response_logger

    def flush_record(self, dialog_id: str):
        workflow_record = self.workflow_manager.flush_record(dialog_id)
        return workflow_record

    async def register_msg(self, utterance: str, user_telegram_id: Hashable,
                           user_device_type: Any, location: Any,
                           channel_type: str, deadline_timestamp=None,
                           require_response=False, **kwargs):
        dialog = await self.state_manager.get_or_create_dialog_by_tg_id(user_telegram_id, channel_type)
        dialog_id = str(dialog.id)
        service = self.pipeline.get_service_by_name('input')
        message_attrs = kwargs.pop('message_attrs', {})

        if require_response:
            event = asyncio.Event()
            kwargs['event'] = event
            kwargs['hold_flush'] = True

        self.workflow_manager.add_workflow_record(
            dialog=dialog, deadline_timestamp=deadline_timestamp, **kwargs)
        task_id = self.workflow_manager.add_task(dialog_id, service, utterance, 0)
        self._response_logger.log_start(task_id, {'dialog': dialog}, service)
        await self.process(task_id, utterance, message_attrs=message_attrs)

        if require_response:
            await event.wait()
            return self.flush_record(dialog_id)

    async def process(self, task_id, response: Any = None, **kwargs):
        workflow_record, task_data = self.workflow_manager.complete_task(task_id, response, **kwargs)
        service = task_data['service']

        if "dialog_object" not in response:
            logger.info(f"Service {service.label}: {response}")

        self._response_logger.log_end(task_id, workflow_record, service)

        if isinstance(response, Exception):
            self.flush_record(workflow_record['dialog'].id)
            raise response

        response_data = service.apply_response_formatter(response)
        # Updating workflow with service response
        if service.state_processor_method:
            await service.state_processor_method(
                dialog=workflow_record['dialog'], payload=response_data,
                label=service.label,
                message_attrs=kwargs.pop('message_attrs', {}), ind=task_data['ind']
            )

        # Flush record  and return zero next services if service is is_responder
        if service.is_responder():
            if not workflow_record.get('hold_flush'):
                self.flush_record(workflow_record['dialog'].id)
            return

        # Calculating next steps
        done, waiting, skipped = self.workflow_manager.get_services_status(workflow_record['dialog'].id)
        next_services = self.pipeline.get_next_services(done.union(skipped), waiting)
        # Processing the case, when service is a skill selector
        if service and service.is_sselector():
            selected_services = response_data
            result = []
            for service in next_services:
                if service.label not in selected_services:
                    self.workflow_manager.skip_service(workflow_record['dialog'].id, service)
                else:
                    result.append(service)
            next_services = result
        # send dialog workflow record to further logging operations:

        service_requests = []
        for service in next_services:
            tasks = service.apply_dialog_formatter(workflow_record)
            for ind, task_data in enumerate(tasks):
                task_id = self.workflow_manager.add_task(workflow_record['dialog'].id, service, task_data, ind)
                self._response_logger.log_start(task_id, workflow_record, service)
                service_requests.append(
                    service.connector_func(payload={'task_id': task_id, 'payload': task_data}, callback=self.process)
                )

        await asyncio.gather(*service_requests)
