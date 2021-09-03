import logging
import sys
import time

from fastapi import FastAPI
import uvicorn

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import ignore_logger

from comet_commonsense.interface import COMeTFactory
from comet_commonsense.config import settings

ignore_logger("root")

sentry_sdk.init(dsn=settings.SENTRY_DSN)

app = FastAPI()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sys.stdout.write = logger.debug

logger.info(f"Loading model for {settings.GRAPH} graph...")
comet_engine = COMeTFactory(settings.GRAPH)(settings.PRETRAINED_MODEL,
                                            settings.CUDA_VISIBLE_DEVICES,
                                            settings.DECODING_ALGO)


def handler(data, func):
    start_time = time.time()
    result = func(data)
    total_time = time.time() - start_time
    logger.info(f"{settings.SERVICE_NAME} exec time = {total_time:.3f}s")
    return result


@app.post("/comet", response_model=comet_engine.response_model)
async def comet_base_handler(input_event: comet_engine.input_event_model):
    result = handler(input_event, comet_engine.process_request)
    return result


@app.post("/comet_annotator", response_model=comet_engine.annotator_response_model)
async def comet_annotator_handler(input_event: comet_engine.annotator_input_model):
    result = handler(input_event, comet_engine.annotator)
    return result


app = SentryAsgiMiddleware(app)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT, log_level="info")
