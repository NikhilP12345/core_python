from celery import Celery
from common.logger import *
from common.tracing import *

setup_tracing(app = None, service_name="example_service", sampling_rate = 1)
add_trace_context_to_loguru()
app = Celery('celery_module', broker='amqps://ffhutvmp:VjuhaeQxoIR8Qqx4vnaPwC9o1yU8o7mM@puffin.rmq2.cloudamqp.com/ffhutvmp')

app.config_from_object('celery_module.celery_config')