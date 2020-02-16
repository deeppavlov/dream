import logging
import logging.config
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from core.service import Service

agent_path = Path(__file__).resolve().parents[1]


def init_logger():
    log_config_path = agent_path / 'log_config.yml'

    with log_config_path.open('r') as f:
        log_config = yaml.safe_load(f)

    log_dir_path = agent_path / 'logs'
    log_dir_path.mkdir(exist_ok=True)

    configured_loggers = [log_config.get('root', {})] + [logger for logger in
                                                         log_config.get('loggers', {}).values()]

    used_handlers = {handler for log in configured_loggers for handler in log.get('handlers', [])}

    for handler_id, handler in list(log_config['handlers'].items()):
        if handler_id not in used_handlers:
            del log_config['handlers'][handler_id]
        elif 'filename' in handler.keys():
            filename = handler['filename']

            if filename[0] == '~':
                logfile_path = Path(filename).expanduser().resolve()
            elif filename[0] == '/':
                logfile_path = Path(filename).resolve()
            else:
                logfile_path = agent_path / filename

            handler['filename'] = str(logfile_path)

    logging.config.dictConfig(log_config)


class BaseResponseLogger:

    def log_start(self, task_id: str, workflow_record: dict, service: Service) -> None:
        raise NotImplementedError

    def log_end(self, task_id: str, workflow_record: dict, service: Service) -> None:
        raise NotImplementedError


class LocalResponseLogger(BaseResponseLogger):
    _enabled: bool
    _logger: logging.Logger

    def __init__(self, enabled: bool, cleanup_timedelta: int = 300) -> None:
        self._services_load = defaultdict(int)
        self._services_response_time = defaultdict(dict)
        self._tasks_buffer = dict()
        self._enabled = enabled
        self._timedelta = timedelta(seconds=cleanup_timedelta)

        if self._enabled:
            self._logger = logging.getLogger('service_logger')
            self._logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler(agent_path / f'logs/{datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S_%f")}.log')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(message)s'))
            self._logger.addHandler(fh)

    def _log(self, time: datetime, task_id: str, workflow_record: dict, service: Service, status: str) -> None:
        # service_name = service.name
        # dialog_id = workflow_record['dialog'].id
        # self._logger.debug(f"{time.strftime('%Y-%m-%d %H:%M:%S.%f')}\t"
        #                    f"{dialog_id}\t{task_id}\t{status}\t{service_name}")
        pass

    def _cleanup(self, time):
        time_threshold = time - self._timedelta

        for key in list(self._tasks_buffer.keys()):
            if self._tasks_buffer[key] < time_threshold:
                del self._tasks_buffer[key]
            else:
                break

        for service_response_time in self._services_response_time.values():
            for start_time in list(service_response_time.keys()):
                if start_time < time_threshold:
                    del service_response_time[start_time]
                else:
                    break

    def log_start(self, task_id: str, workflow_record: dict, service: Service) -> None:
        start_time = datetime.utcnow()

        if service.is_input():
            self._services_load['agent'] += 1
            self._tasks_buffer[workflow_record['dialog'].id] = start_time
        elif not service.is_responder():
            self._tasks_buffer[task_id] = start_time
            self._services_load[service.label] += 1

        if self._enabled:
            self._log(start_time, task_id, workflow_record, service, 'start')

    def log_end(self, task_id: str, workflow_record: dict, service: Service, cancelled=False) -> None:
        end_time = datetime.utcnow()

        if service.is_responder():
            self._services_load['agent'] -= 1
            start_time = self._tasks_buffer.pop(workflow_record['dialog'].id, None)
            if start_time is not None and not cancelled:
                self._services_response_time['agent'][start_time] = (end_time - start_time).total_seconds()
        elif not service.is_input():
            start_time = self._tasks_buffer.pop(task_id, None)
            if start_time is not None:
                self._services_load[service.label] -= 1
                if not cancelled:
                    response_time = (end_time - start_time).total_seconds()
                    self._services_response_time[service.label][start_time] = response_time
                    self._logger.debug(f'{service.label}\t{round(response_time, 5)}\tseconds')
        self._cleanup(end_time)
        if self._enabled:
            self._log(end_time, task_id, workflow_record, service, 'end\t')

    def get_current_load(self):
        self._cleanup(datetime.now())
        response_time = {}
        for service_name, time_dict in self._services_response_time.items():
            sm = sum(time_dict.values())
            ct = len(time_dict)
            response_time[service_name] = sm / ct if ct else 0
        response = {
            'current_load': dict(self._services_load),
            'response_time': response_time
        }
        return response
