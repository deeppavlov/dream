import logging
from collections import defaultdict
from time import time
from typing import Dict, List, Optional
from uuid import uuid4

from core.service import Service
from core.state_schema import Dialog

workflow_logger = logging.getLogger('workflow_logger')


class WorkflowManager:
    def __init__(self):
        self.tasks = defaultdict(dict)
        self.workflow_records = defaultdict(dict)

    def add_workflow_record(self, dialog: Dialog, deadline_timestamp: Optional[float] = None, **kwargs) -> None:
        if str(dialog.id) in self.workflow_records.keys():
            workflow_logger.exception(f"Dialog with id {dialog.id} is already in workflow. Current phrase is: "
                                      f'"{self.workflow_records[str(dialog.id)]["dialog"].utterances[-1].text}"')
            self.get_services_status(str(dialog.id))
            raise ValueError(f'dialog with id {dialog.id} is already in workflow')
        workflow_record = {'dialog': dialog, 'services': defaultdict(dict), 'tasks': dict()}
        if deadline_timestamp:
            workflow_record['deadline_timestamp'] = deadline_timestamp
        workflow_record.update(kwargs)
        self.workflow_records[str(dialog.id)] = workflow_record

    def get_workflow_record(self, dialog_id):
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record:
            return workflow_record
        return None

    def get_dialog_by_id(self, dialog_id: str) -> Dialog:
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record:
            return workflow_record['dialog']
        return None

    def add_task(self, dialog_id: str, service: Service, payload: Dict, ind: int) -> str:
        workflow_record = self.workflow_records.get(dialog_id, None)
        if not workflow_record:
            return None
        task_id = uuid4().hex
        task_data = {'service': service, 'payload': payload, 'dialog': dialog_id, 'ind': ind}
        if service.name not in workflow_record['services']:
            workflow_record['services'][service.name] = {'pending_tasks': set(), 'done': False, 'skipped': False}
        workflow_record['services'][service.name][task_id] = {
            'send': True, 'done': False, 'error': False,
            'agent_send_time': time(), 'agent_done_time': None
        }

        workflow_record['services'][service.name]['pending_tasks'].add(task_id)
        workflow_record['tasks'][task_id] = {'task_data': task_data, 'task_object': None}
        self.tasks[task_id] = task_data
        return task_id

    def set_task_object(self, dialog_id, task_id, task_object):
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record and task_id in workflow_record['tasks']:
            workflow_record['tasks'][task_id]['task_object'] = task_object

    def set_timeout_response_task(self, dialog_id, task_object):
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record:
            workflow_record['timeout_response_task'] = task_object

    def get_pending_tasks(self, dialog_id):
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record:
            return workflow_record['tasks']

    def skip_service(self, dialog_id: str, service: Service) -> None:
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record:
            if service in workflow_record['services']:
                workflow_record['services'][service.name]['skipped'] = True
            else:
                workflow_record['services'][service.name] = {'pending_tasks': set(), 'done': False, 'skipped': True}
        workflow_logger.info(f'service {service.name} was skipped from pipeline for {dialog_id}')

    def get_services_status(self, dialog_id: str) -> List:
        workflow_record = self.workflow_records.get(dialog_id, None)
        if not workflow_record:
            return set(), set(), set()
        done = set()
        waiting = set()
        skipped = set()
        for k, v in workflow_record['services'].items():
            if v['skipped'] or v.get('error', False):
                skipped.add(k)
            elif v['done']:
                done.add(k)
            else:
                waiting.add(k)
        workflow_logger.info(f'Current processing status for {dialog_id}: {done}, {waiting}, {skipped}')
        return done, waiting, skipped

    def complete_task(self, task_id, response, **kwargs) -> Dict:
        task = self.tasks.pop(task_id, None)
        if not task:
            workflow_logger.debug(f'task with id: {task_id} was not found in workflow')
            return None, None

        workflow_record = self.workflow_records.get(task['dialog'], None)
        if not workflow_record:
            workflow_record = task.pop('workflow_record', None)
            workflow_logger.debug(f"task {task_id}:{task['service'].name} was finished, "
                                  f"but corresponding workflow record was flushed earlier")
            return workflow_record, task

        workflow_record['tasks'].pop(task_id)
        workflow_record['services'][task['service'].name]['pending_tasks'].discard(task_id)

        if not workflow_record['services'][task['service'].name]['pending_tasks']:
            workflow_record['services'][task['service'].name]['done'] = True
        workflow_record['services'][task['service'].name][task_id]['agent_done_time'] = time()

        if isinstance(response, Exception):
            workflow_record['services'][task['service'].name][task_id]['error'] = True
            if not workflow_record['services'][task['service'].name]['pending_tasks']:
                workflow_record['services'][task['service'].name]['error'] = True
        else:
            workflow_record['services'][task['service'].name][task_id]['done'] = True
        workflow_record['services'][task['service'].name][task_id].update(**kwargs)
        workflow_logger.debug(f"task {task_id}:{task['service'].name} from {task['dialog']} was finished")
        return workflow_record, task

    def flush_record(self, dialog_id: str) -> Dict:
        workflow_record = self.workflow_records.pop(dialog_id, None)
        if not workflow_record:
            return None
        for i in workflow_record.pop('tasks', {}).keys():
            self.tasks[i]['workflow_record'] = workflow_record
        workflow_logger.info(f'A record for {dialog_id} was successfully flushed from workflow')
        return workflow_record
