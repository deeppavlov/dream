from itertools import chain
from copy import deepcopy

import aiohttp
import asyncio

from core.transform_config import SKILLS, ANNOTATORS_1, ANNOTATORS_2, ANNOTATORS_3, SKILL_SELECTORS, \
    RESPONSE_SELECTORS, POSTPROCESSORS
from core.connectors import HTTPConnector, ConfidenceResponseSelectorConnector, AioQueueConnector, \
    QueueListenerBatchifyer, AgentGatewayToServiceConnector
from core.pipeline import simple_workflow_formatter
from core.service import Service
from core.state_manager import StateManager
from core.transport.settings import TRANSPORT_SETTINGS


def prepare_agent_gateway(on_channel_callback=None, on_service_callback=None):
    from core.transport.mapping import GATEWAYS_MAP
    transport_type = TRANSPORT_SETTINGS['transport']['type']
    gateway_cls = GATEWAYS_MAP[transport_type]['agent']
    return gateway_cls(config=TRANSPORT_SETTINGS,
                       on_service_callback=on_service_callback,
                       on_channel_callback=on_channel_callback)


def add_bot_to_name(name):
    return f'bot_{name}'


def parse_old_config():
    services = []
    worker_tasks = []
    session = None
    gateway = None

    def make_service_from_config_rec(conf_record, sess, state_processor_method, tags, names_previous_services,
                                     gate, name_modifier=None):
        _worker_tasks = []
        if name_modifier:
            name = name_modifier(conf_record['name'])
        else:
            name = conf_record['name']
        formatter = conf_record['formatter']
        batch_size = conf_record.get('batch_size', 1)
        url = conf_record['url']

        connector_func = None

        if conf_record['protocol'] == 'http':
            sess = sess or aiohttp.ClientSession()
            if batch_size == 1 and isinstance(url, str):
                connector_func = HTTPConnector(sess, url, formatter, name).send
            else:
                queue = asyncio.Queue()
                connector_func = AioQueueConnector(queue).send  # worker task and queue connector
                if isinstance(url, str):
                    urls = [url]
                else:
                    urls = url
                for u in urls:
                    _worker_tasks.append(QueueListenerBatchifyer(sess, u, formatter,
                                                                 name, queue, batch_size))

        elif conf_record['protocol'] == 'AMQP':
            gate = gate or prepare_agent_gateway()
            connector_func = AgentGatewayToServiceConnector(to_service_callback=gate.send_to_service,
                                                            service_name=name).send

        if connector_func is None:
            raise ValueError(f'No connector function is defined while making a service {name}.')

        _service = Service(name, connector_func, state_processor_method, batch_size,
                           tags, names_previous_services, simple_workflow_formatter)

        return _service, _worker_tasks, sess, gate

    for anno in ANNOTATORS_1:
        service, workers, session, gateway = make_service_from_config_rec(anno, session,
                                                                          StateManager.add_annotation_dict,
                                                                          ['ANNOTATORS_1'], set(), gateway)
        services.append(service)
        worker_tasks.extend(workers)

    previous_services = {i.name for i in services if 'ANNOTATORS_1' in i.tags}

    if ANNOTATORS_2:
        for anno in ANNOTATORS_2:
            service, workers, session, gateway = make_service_from_config_rec(anno, session,
                                                                              StateManager.add_annotation_dict,
                                                                              ['ANNOTATORS_2'], previous_services,
                                                                              gateway)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'ANNOTATORS_2' in i.tags}

    if ANNOTATORS_3:
        for anno in ANNOTATORS_3:
            service, workers, session, gateway = make_service_from_config_rec(anno, session,
                                                                              StateManager.add_annotation_dict,
                                                                              ['ANNOTATORS_3'], previous_services,
                                                                              gateway)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'ANNOTATORS_3' in i.tags}

    if SKILL_SELECTORS:
        for ss in SKILL_SELECTORS:
            service, workers, session, gateway = make_service_from_config_rec(ss, session, StateManager.do_nothing,
                                                                              ['SKILL_SELECTORS', 'selector'],
                                                                              previous_services, gateway)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'SKILL_SELECTORS' in i.tags}

    if SKILLS:
        for s in SKILLS:
            service, workers, session, gateway = make_service_from_config_rec(s, session,
                                                                              StateManager.add_hypothesis_dict,
                                                                              ['SKILLS'], previous_services, gateway)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'SKILLS' in i.tags}

    if not RESPONSE_SELECTORS:
        services.append(
            Service(
                'confidence_response_selector',
                ConfidenceResponseSelectorConnector('confidence_response_selector').send,
                StateManager.add_bot_utterance_simple_dict,
                1, ['RESPONSE_SELECTORS'], previous_services, simple_workflow_formatter
            )
        )
    else:
        for r in RESPONSE_SELECTORS:
            service, workers, session, gateway = \
                make_service_from_config_rec(r, session,
                                             StateManager.add_bot_utterance_simple_dict,
                                             ['RESPONSE_SELECTORS'], previous_services,
                                             gateway)
            services.append(service)
            worker_tasks.extend(workers)

    previous_services = {i.name for i in services if 'RESPONSE_SELECTORS' in i.tags}

    if POSTPROCESSORS:
        for p in POSTPROCESSORS:
            service, workers, session, gateway = make_service_from_config_rec(p, session, StateManager.add_text_dict,
                                                                              ['POSTPROCESSORS'], previous_services,
                                                                              gateway)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'POSTPROCESSORS' in i.tags}

    if ANNOTATORS_1:
        for anno in ANNOTATORS_1:
            service, workers, session, gateway = make_service_from_config_rec(anno, session,
                                                                              StateManager.add_annotation_dict,
                                                                              ['POST_ANNOTATORS_1'], previous_services,
                                                                              gateway, add_bot_to_name)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'POST_ANNOTATORS_1' in i.tags}

    if ANNOTATORS_2:
        for anno in ANNOTATORS_2:
            service, workers, session, gateway = make_service_from_config_rec(anno, session,
                                                                              StateManager.add_annotation_dict,
                                                                              ['POST_ANNOTATORS_2'], previous_services,
                                                                              gateway, add_bot_to_name)
            services.append(service)
            worker_tasks.extend(workers)

        previous_services = {i.name for i in services if 'POST_ANNOTATORS_2' in i.tags}

    for anno in ANNOTATORS_3:
        service, workers, session, gateway = make_service_from_config_rec(anno, session,
                                                                          StateManager.add_annotation_dict,
                                                                          ['POST_ANNOTATORS_3'],
                                                                          previous_services, gateway, add_bot_to_name)
        services.append(service)
        worker_tasks.extend(workers)

    return services, worker_tasks, session, gateway


def get_service_gateway_config(service_name):
    for config in chain(SKILLS, ANNOTATORS_1, ANNOTATORS_2, ANNOTATORS_3,
                        SKILL_SELECTORS, RESPONSE_SELECTORS, POSTPROCESSORS):
        config_name = config['name']

        if config_name == service_name:
            matching_config = config
            break
    else:
        raise ValueError(f'Config for service {service_name} was not found')

    gateway_config = deepcopy(TRANSPORT_SETTINGS)
    gateway_config['service'] = matching_config

    # TODO think if we can remove this workaround for bot annotators
    if service_name in [service['name'] for service in chain(ANNOTATORS_1, ANNOTATORS_2, ANNOTATORS_3)]:
        gateway_config['service']['names'] = [service_name, add_bot_to_name(service_name)]

    return gateway_config
