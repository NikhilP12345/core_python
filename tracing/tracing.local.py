from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def implement_tracing(app, excluded_urls=""):
	# Instruments Flask
	FlaskInstrumentor().instrument_app(app, excluded_urls=excluded_urls)
	# Instruments requests
	RequestsInstrumentor().instrument()
	# Instruments urllib
	URLLibInstrumentor().instrument()
	# Instruments redis
	RedisInstrumentor().instrument()
	trace.set_tracer_provider(TracerProvider())	
	
	#### commenting out to reduce noise, uncomment these lines to print detailed trace object to the console
	# trace.get_tracer_provider().add_span_processor(
	#     BatchSpanProcessor(ConsoleSpanExporter())
	# )

def inject_trace_into_logs(service_name):
    LoggingInstrumentor().instrument(set_logging_format=True)