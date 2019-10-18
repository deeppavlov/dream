import logging
import logging.config
from pathlib import Path

import yaml


def init_logger():
    agent_path = Path(__file__).resolve().parent.parent
    log_config_path = agent_path / 'log_config.yml'

    with log_config_path.open('r') as f:
        log_config = yaml.safe_load(f)

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
