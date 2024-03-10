from flask import Flask, request
from loguru import logger
from common.exception import CoreApi

from common.logger import *
from common.tracing import *
from views.test import TestHandler
from opentelemetry import trace


# Initialize your Flask app
app = Flask(__name__)

# Setup tracing and logging
setup_tracing(app, service_name="example_service", sampling_rate = 1)
add_trace_context_to_loguru()
tracer = trace.get_tracer(__name__)

@app.before_request
def start_span():
    # Start a span with the current request information
    flask_request = request
    span_name = f"{flask_request.method} {flask_request.path}"
    ctx = trace.set_span_in_context(trace.INVALID_SPAN)
    span = tracer.start_span(span_name, context=ctx)
    trace.use_span(span, end_on_exit=False)

@app.after_request
def end_span(response):
    # End the span started in before_request
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute("http.status_code", response.status_code)
        current_span.end()
    return response


api = CoreApi(app, catch_all_404s=True)


TestHandler.init(api)


if __name__ == "__main__":
    app.run(debug=True, port=8081)
