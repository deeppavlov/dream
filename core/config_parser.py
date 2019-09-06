import aiohttp

from core.transform_config import SKILLS, ANNOTATORS_1, ANNOTATORS_2, ANNOTATORS_3, SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS
from core.connectors import HTTPConnector, ConfidenceResponseSelectorConnector
from core.pipeline import Service, simple_workflow_formatter
from core.state_manager import StateManager


services = []
worker_tasks = []


def make_service_from_config_rec(log_record, session, state_processor_method, tags, names_previous_services, name_modifier=None):
    worker_task = None
    if name_modifier:
        name = name_modifier(log_record['name'])
    else:
        name = log_record['name']
    formatter = log_record['formatter']
    batch_size = log_record.get('batch_size', 1)
    if log_record['protocol'] == 'http':
        if log_record.get('external', False):
            url = f"http://{log_record['host']}:{log_record['port']}/{log_record['endpoint']}"
        else:
            url = f"http://{log_record['name']}:{log_record['port']}/{log_record['endpoint']}"
        if batch_size == 1:
            connector = HTTPConnector(session, url, formatter, log_record['name'])
        else:
            pass  # worker task and queue connector

    service = Service(name, connector, state_processor_method, batch_size,
                      tags, names_previous_services, simple_workflow_formatter)
    return service, worker_task


def add_bot_to_name(name):
    return f'bot_{name}'


session = aiohttp.ClientSession()

for anno in ANNOTATORS_1:
    service, worker_task = make_service_from_config_rec(anno, session, StateManager.add_annotation,
                                                        ['ANNOTATORS_1'], set())
    services.append(service)
    worker_tasks.append(worker_task)

previous_services = {i.name for i in services if 'ANNOTATORS_1' in i.tags}

if ANNOTATORS_2:
    for anno in ANNOTATORS_2:
        service, worker_task = make_service_from_config_rec(anno, session, StateManager.add_annotation,
                                                            ['ANNOTATORS_2'], previous_services)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'ANNOTATORS_2' in i.tags}

if ANNOTATORS_3:
    for anno in ANNOTATORS_3:
        service, worker_task = make_service_from_config_rec(anno, session, StateManager.add_annotation,
                                                            ['ANNOTATORS_3'], previous_services)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'ANNOTATORS_3' in i.tags}

if SKILL_SELECTORS:
    for ss in SKILL_SELECTORS:
        service, worker_task = make_service_from_config_rec(ss, session, StateManager.do_nothing,
                                                            ['SKILL_SELECTORS', 'selector'], previous_services)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'SKILL_SELECTORS' in i.tags}

if SKILLS:
    for s in SKILLS:
        service, worker_task = make_service_from_config_rec(s, session, StateManager.add_selected_skill,
                                                            ['SKILLS'], previous_services)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'SKILLS' in i.tags}

if not RESPONSE_SELECTORS:
    services.append(Service('confidence_response_selector', ConfidenceResponseSelectorConnector(),
                            StateManager.add_bot_utterance_simple,
                            1, ['RESPONSE_SELECTORS'], previous_services, simple_workflow_formatter))
else:
    for r in RESPONSE_SELECTORS:
        service, worker_task = make_service_from_config_rec(r, session, StateManager.add_bot_utterance_simple,
                                                            ['RESPONSE_SELECTORS'], previous_services)
        services.append(service)
        worker_tasks.append(worker_task)

previous_services = {i.name for i in services if 'RESPONSE_SELECTORS' in i.tags}

if POSTPROCESSORS:
    for p in POSTPROCESSORS:
        service, worker_task = make_service_from_config_rec(p, session, StateManager.add_text,
                                                            ['POSTPROCESSORS'], previous_services)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'POSTPROCESSORS' in i.tags}

if ANNOTATORS_1:
    for anno in ANNOTATORS_1:
        service, worker_task = make_service_from_config_rec(anno, session, StateManager.add_annotation,
                                                            ['POST_ANNOTATORS_1'], previous_services, add_bot_to_name)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'POST_ANNOTATORS_1' in i.tags}

if ANNOTATORS_2:
    for anno in ANNOTATORS_2:
        service, worker_task = make_service_from_config_rec(anno, session, StateManager.add_annotation,
                                                            ['POST_ANNOTATORS_2'], previous_services, add_bot_to_name)
        services.append(service)
        worker_tasks.append(worker_task)

    previous_services = {i.name for i in services if 'POST_ANNOTATORS_2' in i.tags}

for anno in ANNOTATORS_3:
    service, worker_task = make_service_from_config_rec(anno, session, StateManager.add_annotation, ['POST_ANNOTATORS_3'],
                                                        previous_services, add_bot_to_name)
    services.append(service)
    worker_tasks.append(worker_task)
