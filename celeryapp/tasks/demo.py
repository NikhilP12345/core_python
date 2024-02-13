import logging
import time

from celeryapp.celery import app

logger = logging.getLogger(__name__)


MOCK_DELAY_SECONDS = 10


@app.task
def demo_celery(*args, **kwargs):
    logger.info("Celery task invoked with args=%s and kwargs=%s", args, kwargs)

    logger.info("Mocking processing time with a %s seconds delay...", MOCK_DELAY_SECONDS)
    time.sleep(MOCK_DELAY_SECONDS)

    return {
        "someKey": "someValue",
        "args": args,
        "kwargs": kwargs,
    }
