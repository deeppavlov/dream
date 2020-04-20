import asyncio
from time import time
from typing import Any, Hashable

from core.log import BaseResponseLogger
from core.pipeline import Pipeline
from core.state_manager import StateManager
from core.workflow_manager import WorkflowManager

import logging
from os import getenv
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

sentry_sdk.init(dsn=getenv('SENTRY_DSN'), integrations=[AioHttpIntegration()])
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
        if 'timeout_response_task' in workflow_record:
            workflow_record['timeout_response_task'].cancel()
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
        asyncio.create_task(self.process(task_id, utterance, message_attrs=message_attrs))
        if deadline_timestamp:
            self.workflow_manager.set_timeout_response_task(
                dialog_id, asyncio.create_task(self.timeout_process(dialog_id, deadline_timestamp))
            )

        if require_response:
            await event.wait()
            return self.flush_record(dialog_id)

    async def process(self, task_id, response: Any = None, **kwargs):
        workflow_record, task_data = self.workflow_manager.complete_task(task_id, response, **kwargs)
        if not workflow_record:
            return
        service = task_data['service']
        logger.info(f"Service {service.label}: {response}")
        self._response_logger.log_end(task_id, workflow_record, service)

        if service.label in set(['last_chance_service', 'timeout_service']):
            # extract services from workflow_record and group them by status
            done = [k for k, v in workflow_record['services'].items() if v['done'] and not v.get('error', False)]
            in_progress = [k for k, v in workflow_record['services'].items()
                           if not v['done'] and not v.get('error', False)]
            with_errors = [k for k, v in workflow_record['services'].items() if v.get('error', False)]
            with sentry_sdk.push_scope() as scope:
                scope.set_extra('user_id', workflow_record['dialog'].human.telegram_id)
                scope.set_extra('dialog_id', workflow_record['dialog'].id)
                scope.set_extra('response', response)
                scope.set_extra('done', done)
                scope.set_extra('in_progress', in_progress)
                scope.set_extra('with_errors', with_errors)
                sentry_sdk.capture_message(f"{service.label} was called")

        if isinstance(response, Exception):
            logger.exception(response)
            sentry_sdk.capture_exception(response)
            # Skip all services, which are depends on failured one (if exception is not from task cancelling)
            if not isinstance(response, asyncio.CancelledError):
                for i in service.dependent_services:
                    self.workflow_manager.skip_service(workflow_record['dialog'].id, i)
        else:
            response_data = service.apply_response_formatter(response)
            # Updating workflow with service response
            if service.state_processor_method:
                await service.state_processor_method(
                    dialog=workflow_record['dialog'], payload=response_data,
                    label=service.label,
                    message_attrs=kwargs.pop('message_attrs', {}), ind=task_data['ind']
                )

            # Processing the case, when service is a skill selector
            if service and service.is_sselector():
                skipped_services = {s for s in service.next_services if s.label not in set(response_data)}

                for s in skipped_services:
                    self.workflow_manager.skip_service(workflow_record['dialog'].id, s)

            # Flush record  and return zero next services if service is is_responder
            elif service.is_responder():
                if not workflow_record.get('hold_flush'):
                    self.flush_record(workflow_record['dialog'].id)
                return

        # Calculating next steps
        done, waiting, skipped = self.workflow_manager.get_services_status(workflow_record['dialog'].id)
        next_services = self.pipeline.get_next_services(done, waiting, skipped)

        await self.create_processing_tasks(workflow_record, next_services)

    async def create_processing_tasks(self, workflow_record, next_services):
        for service in next_services:
            tasks = service.apply_dialog_formatter(workflow_record)
            for ind, task_data in enumerate(tasks):
                task_id = self.workflow_manager.add_task(workflow_record['dialog'].id, service, task_data, ind)
                self._response_logger.log_start(task_id, workflow_record, service)
                self.workflow_manager.set_task_object(
                    workflow_record['dialog'].id,
                    task_id,
                    asyncio.create_task(
                        service.connector_func(
                            payload={'task_id': task_id, 'payload': task_data}, callback=self.process
                        )
                    )
                )

    async def timeout_process(self, dialog_id, deadline_timestamp):
        await asyncio.sleep(deadline_timestamp - time())
        workflow_record = self.workflow_manager.get_workflow_record(dialog_id)
        if not workflow_record:
            return
        next_services = [self.pipeline.timeout_service]
        for k, v in self.workflow_manager.get_pending_tasks(dialog_id).items():
            v['task_object'].cancel()
            self._response_logger.log_end(k, workflow_record, v['task_data']['service'], True)

        asyncio.ensure_future(self.create_processing_tasks(workflow_record, next_services))
