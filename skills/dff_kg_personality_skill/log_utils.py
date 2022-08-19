import logging


def create_logger(
    name: str,
    fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level: str = "INFO",
) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
