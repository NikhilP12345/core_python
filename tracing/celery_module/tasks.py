from celery_module.celery import app
from opentelemetry import trace, propagate
from opentelemetry.propagate import extract
from opentelemetry.trace import set_span_in_context
from loguru import logger



@app.task(bind=True)
def printHello(self, full_payload):
    task_payload = full_payload['task_payload']
    trace_context = full_payload['trace_context']
    context = extract(trace_context)
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("printHello", context=context) as span:
        # Now, this block runs under the extracted trace context
        task_payload = full_payload['task_payload']
        x, y = task_payload['x'], task_payload['y']
        logger.info({"x": x, "y": y})
