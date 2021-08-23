import unittest
from core.workflow_manager import WorkflowManager
from uuid import uuid4


class TestDialog:
    def __init__(self, id):
        self.id = id


class TestService:
    def __init__(self, name):
        self.name = name


class TestWorkflowManagerDialog(unittest.TestCase):
    def setUp(self):
        self.workflow = WorkflowManager()
        self.dialog_id = uuid4().hex
        self.workflow.add_workflow_record(TestDialog(self.dialog_id))

    def test_internal_params(self):
        self.assertTrue(self.dialog_id in self.workflow.workflow_records)
        self.assertEqual(1, len(self.workflow.workflow_records))

    def test_get_record(self):
        self.assertEqual(self.workflow.get_dialog_by_id(self.dialog_id).id, self.dialog_id, 'get_dialog works wrong')

    def test_add_another_dialog(self):
        another_dialog_id = uuid4().hex
        self.workflow.add_workflow_record(TestDialog(another_dialog_id))
        self.assertTrue(self.dialog_id in self.workflow.workflow_records)
        self.assertTrue(another_dialog_id in self.workflow.workflow_records)
        self.assertEqual(2, len(self.workflow.workflow_records))

    def test_add_duplicate_dialog(self):
        with self.assertRaises(ValueError):
            self.workflow.add_workflow_record(TestDialog(self.dialog_id))

    def test_flush_record(self):
        workflow_record = self.workflow.flush_record(self.dialog_id)
        self.assertTrue(isinstance(workflow_record, dict))
        self.assertEqual(workflow_record['dialog'].id, self.dialog_id)

    def test_add_task(self):
        payload = uuid4().hex
        task_service = TestService('testservice')
        task_id = self.workflow.add_task(self.dialog_id, task_service, payload, 1)
        self.assertTrue(task_id is not None)
        self.assertEqual(1, len(self.workflow.tasks))
        self.assertTrue(task_id in self.workflow.tasks)

    def test_complete_task(self):
        payload = uuid4().hex
        response = '123'
        task_service = TestService('testservice')
        task_id = self.workflow.add_task(self.dialog_id, task_service, payload, 1)
        workflow_record, task = self.workflow.complete_task(task_id, response)
        self.assertTrue(isinstance(task, dict))
        self.assertTrue(isinstance(workflow_record, dict))
        self.assertEqual(task['service'].name, task_service.name)
        self.assertEqual(task['dialog'], workflow_record['dialog'].id)

    def test_double_complete_task(self):
        payload = uuid4().hex
        response = '123'
        task_service = TestService('testservice')
        task_id = self.workflow.add_task(self.dialog_id, task_service, payload, 1)
        self.workflow.complete_task(task_id, response)
        workflow_record, task = self.workflow.complete_task(task_id, response)
        self.assertTrue(workflow_record is None)
        self.assertTrue(task is None)

    def test_next_tasks(self):
        payload = uuid4().hex
        response = '123'
        done_service = TestService(uuid4().hex)
        waiting_service = TestService(uuid4().hex)
        skipped_service = TestService(uuid4().hex)

        self.workflow.skip_service(self.dialog_id, skipped_service)
        task_id = self.workflow.add_task(self.dialog_id, done_service, payload, 1)
        self.workflow.complete_task(task_id, response)
        self.workflow.add_task(self.dialog_id, waiting_service, payload, 1)

        done, waiting, skipped = self.workflow.get_services_status(self.dialog_id)
        self.assertTrue(done_service.name in done)
        self.assertTrue(waiting_service.name in waiting)
        self.assertTrue(skipped_service.name in skipped)

    def test_flush(self):
        payload = uuid4().hex
        response = '123'
        done_service = TestService(uuid4().hex)
        waiting_service = TestService(uuid4().hex)
        skipped_service = TestService(uuid4().hex)

        self.workflow.skip_service(self.dialog_id, skipped_service)
        done_task_id = self.workflow.add_task(self.dialog_id, done_service, payload, 1)
        self.workflow.complete_task(done_task_id, response)
        waiting_task_id = self.workflow.add_task(self.dialog_id, waiting_service, payload, 1)

        workflow_record = self.workflow.flush_record(self.dialog_id)
        self.assertEqual(self.dialog_id, workflow_record['dialog'].id)

        workflow_record, late_task = self.workflow.complete_task(waiting_task_id, response)
        self.assertEqual(self.dialog_id, workflow_record['dialog'].id)
        self.assertTrue('dialog' in late_task)
        self.assertEqual(self.dialog_id, late_task['dialog'])


if __name__ == '__main__':
    unittest.main()
