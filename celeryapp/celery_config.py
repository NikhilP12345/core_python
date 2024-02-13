import config
from config.configutils import build_ampq_uri, build_mongo_uri

include = [
    "celeryapp.tasks.demo",
]

broker_url = build_ampq_uri(
    config.CELERY_AMQP_HOST,
    config.CELERY_AMQP_PORT,
    config.CELERY_AMQP_VHOST,
    config.CELERY_AMQP_USER,
    config.CELERY_AMQP_PASSWORD,
)

result_backend = build_mongo_uri(
    config.CELERY_MONGO_HOST,
    config.CELERY_MONGO_PORT,
    config.CELERY_MONGO_DB,
    config.CELERY_MONGO_USER,
    config.CELERY_MONGO_PASSWORD,
)

mongodb_backend_settings = {
    "database": config.CELERY_MONGO_DB,
    "taskmeta_collection": "celery_tasksmeta",
    "retryWrites": True,
    "w": "majority",
}

result_expires = 3600
timezone = "UTC"
task_acks_late = True
task_reject_on_worker_lost = True
