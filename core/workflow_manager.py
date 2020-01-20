from collections import defaultdict
from uuid import uuid4
from typing import Optional, Dict, List
from time import time

from core.state_schema import Dialog
from core.service import Service


class WorkflowManager:
    def __init__(self):
        self.tasks = defaultdict(dict)
        self.workflow_records = defaultdict(dict)

    def add_workflow_record(self, dialog: Dialog, deadline_timestamp: Optional[float] = None, **kwargs) -> None:
        if str(dialog.id) in self.workflow_records.keys():
            raise ValueError(f'dialog with id {dialog.id} is already in workflow')
        workflow_record = {'dialog': dialog, 'services': defaultdict(dict), 'tasks': set()}
        if deadline_timestamp:
            workflow_record['deadline_timestamp'] = deadline_timestamp
        workflow_record.update(kwargs)
        self.workflow_records[str(dialog.id)] = workflow_record

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
        workflow_record['tasks'].add(task_id)
        self.tasks[task_id] = task_data
        return task_id

    def skip_service(self, dialog_id: str, service: Service) -> None:
        workflow_record = self.workflow_records.get(dialog_id, None)
        if workflow_record:
            if service in workflow_record['services']:
                workflow_record['services'][service.name]['skipped'] = True
            else:
                workflow_record['services'][service.name] = {'pending_tasks': set(), 'done': False, 'skipped': True}

    def get_services_status(self, dialog_id: str) -> List:
        workflow_record = self.workflow_records.get(dialog_id, None)
        if not workflow_record:
            return None, None, None
        done = set()
        waiting = set()
        skipped = set()
        for k, v in workflow_record['services'].items():
            if v['skipped']:
                skipped.add(k)
            elif v['done']:
                done.add(k)
            else:
                waiting.add(k)
        return done, waiting, skipped

    def complete_task(self, task_id, response, **kwargs) -> Dict:
        task = self.tasks.pop(task_id, None)
        if not task:
            return None, None

        workflow_record = self.workflow_records.get(task['dialog'], None)
        if not workflow_record:
            workflow_record = task.pop('workflow_record', None)
            return workflow_record, task

        workflow_record['tasks'].discard(task_id)
        workflow_record['services'][task['service'].name]['pending_tasks'].discard(task_id)

        if not workflow_record['services'][task['service'].name]['pending_tasks']:
            workflow_record['services'][task['service'].name]['done'] = True
        workflow_record['services'][task['service'].name][task_id]['agent_done_time'] = time()

        if isinstance(response, Exception):
            workflow_record['services'][task['service'].name][task_id]['error'] = True
        else:
            workflow_record['services'][task['service'].name][task_id]['done'] = True
        workflow_record['services'][task['service'].name][task_id].update(**kwargs)
        return workflow_record, task

    def flush_record(self, dialog_id: str) -> Dict:
        workflow_record = self.workflow_records.pop(dialog_id, None)
        if not workflow_record:
            return None
        for i in workflow_record.pop('tasks', set()):
            self.tasks[i]['workflow_record'] = workflow_record

        return workflow_record
