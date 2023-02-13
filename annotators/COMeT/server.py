import logging
import time
from functools import wraps

from fastapi import FastAPI
import uvicorn

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import ignore_logger

from comet_commonsense.interface import COMeTFactory
from comet_commonsense.config import settings
import test_server

ignore_logger("root")

sentry_sdk.init(dsn=settings.SENTRY_DSN)

app = FastAPI()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

comet_engine = COMeTFactory(settings.GRAPH)(settings.PRETRAINED_MODEL, settings.DECODING_ALGO)


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        total_time = time.time() - ts
        logger.info(f"{settings.SERVICE_NAME} exec time = {total_time:.3f}s")
        return result

    return wrap


@timing
def handler(data):
    try:
        return comet_engine.process_request(data)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        logger.exception(exc)
        raise exc


@timing
def annotator_handler(data):
    try:
        return comet_engine.annotator(data)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        logger.exception(exc)
        raise exc


@app.post("/comet", response_model=comet_engine.response_model)
async def comet_base_handler(input_event: comet_engine.input_event_model):
    result = handler(input_event.dict())
    return result


@app.post("/comet_annotator", response_model=comet_engine.annotator_response_model)
async def comet_annotator_handler(input_event: comet_engine.annotator_input_model):
    result = annotator_handler(input_event.dict())
    logger.info(f"comet_annotator result: {result}")
    return result


app = SentryAsgiMiddleware(app)

try:
    test_server.run_test(handler)
    logger.info("test query processed")
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    logger.exception(exc)
    raise exc

logger.info(f"{settings.SERVICE_NAME} is loaded and ready")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT, log_level="info")
