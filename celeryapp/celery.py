from celery import Celery
from celery.signals import worker_process_init

from core.helpers.cache_helper import CacheHelper
from ndb_client import client
import os
import config as Config

app = Celery("celery_module")

# set config from celery config file
app.config_from_object("celeryapp.celery_config")


@worker_process_init.connect
def worker_process_init_signal_handler(**_):
    # Setup Redis
    CacheHelper.init(
      Config.REDIS_SET_SENTINEL,
      Config.REDIS_DB_NUMBER,
      Config.REDIX_PREFIX_KEY,
      Config.REDIS_SENTINEL_NAME,
      Config.REDIS_HOST,
      Config.REDIS_PORT,
      Config.REDIS_PASSWORD,
      Config.REDIS_SENTINEL_PORT,
      Config.REDIS_SENTINELS,
      Config.REDIS_SENTINEL_PASSWORD,
     )


def task_with_db_context(*task_args, **task_kwargs):
    def decorator(fn):
        @app.task(*task_args, **task_kwargs)
        def decorated(*args, **kwargs):
            with client.context():
                return fn(*args, **kwargs)

        return decorated

    return decorator
