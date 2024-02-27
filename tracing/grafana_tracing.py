from flask import Flask
from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import SpanContext
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


def setup_tracing(service_name="my_service", sampling_rate=1):
    try:
        print(f"In setup_tracing")
        sampler = ParentBasedTraceIdRatio(sampling_rate)
        resource = Resource.create(attributes={SERVICE_NAME: service_name})
        trace_provider = TracerProvider(sampler=sampler, resource=resource)
        trace.set_tracer_provider(trace_provider)
        
        otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")  # Configure for Grafana Tempo
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # console_exporter = ConsoleSpanExporter()
        # console_span_processor = SimpleSpanProcessor(console_exporter)
        # trace.get_tracer_provider().add_span_processor(console_span_processor)


        # Instrumentation
        FlaskInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        URLLibInstrumentor().instrument()
        GrpcInstrumentorServer().instrument()
    except Exception as error:
        print(f"Error in setup_tracing, error: {error}")
        raise error

def add_trace_context_to_loguru():

    def enrich_with_trace_info(record):
        try:
            print(f"In enrich_with_trace_info")
            span = trace.get_current_span()
            if not span:
                # No active span, no action needed
                return

            # Ensure we have a valid span context
            span_context = span.get_span_context()
            if not span_context:
                # No span context available
                return

            # Check if the span is recording or not
            if isinstance(span_context, SpanContext):
                # It's a valid span context, extract trace and span IDs
                trace_id = span_context.trace_id
                span_id = span_context.span_id
                if trace_id != trace.INVALID_TRACE_ID:
                    record["extra"]["otel_trace_id"] = f"{trace_id:032x}"
                else:
                    record["extra"]["otel_trace_id"] = None

                if span_id != trace.INVALID_SPAN_ID:
                    record["extra"]["otel_span_id"] = f"{span_id:016x}"
                else:
                    record["extra"]["otel_span_id"] = None
            else:
                # Handling for non-recording or invalid spans
                record["extra"]["otel_trace_id"] = None
                record["extra"]["otel_span_id"] = None
        except Exception as error:
            print(f"Error in enrich_with_trace_info, error: {error}")
            raise error

    try:
        print(f"In add_trace_context_to_loguru")
        logger.configure(patcher=enrich_with_trace_info)

    except Exception as error:
        print(f"Error in add_trace_context_to_loguru, error: {error}")
        raise error
        

# Initialize your Flask app
app = Flask(__name__)

# Setup tracing and logging
setup_tracing(service_name="example_service")
add_trace_context_to_loguru()
tracer = trace.get_tracer(__name__)

@app.route("/name/as")
def hello():
    try:
        with tracer.start_as_current_span("ABC"):
            print("sfgrg")
            logger.info("Received a request to '/'")
            print("DFbdg")
            return "Hello, World!"
    except Exception as error:
        print(f"Error in hello, error: {error}")
        raise error

if __name__ == "__main__":
    app.run(debug=True, port = 5000)
