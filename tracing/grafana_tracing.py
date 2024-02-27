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
from opentelemetry.trace import SpanContext, INVALID_SPAN_ID, INVALID_TRACE_ID
import requests
import datetime
import json
import time
from decorators import trace_function

def loki_sink(message):
    print(message)
    timestamp_ns = str(int(time.time() * 1e9))  # Current timestamp in nanoseconds
    log_level = message.record["level"].name
    log_message = message.record["message"]
    log_time = message.record["time"].isoformat() 
    data = {
        "streams": [
            {
                "stream": {
                    "service": "example_service",
                    "job": "bot_python",
                    "task_id": "2022-03-01",
                    "type": "execution",
                    "log_level": log_level,
                    "otel_trace_id": message.record["extra"].get("otel_trace_id", "0"*32)
                },
                "values": [
                    [timestamp_ns, f"message: {log_message}"]
                ]
            }
        ]
    }
    print(data)
    headers = {
        "Content-type": "application/json"
    }
    url = "http://localhost:3101/loki/api/v1/push"
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 204:
            print(f"Failed to send log to Loki: {response.text}")
        print(response.__dict__)
        pass
    except Exception as e:
        print(f"Error sending log to Loki: {e}")

def setup_tracing(service_name="my_service", sampling_rate=1):
    print(f"In setup_tracing")
    sampler = ParentBasedTraceIdRatio(sampling_rate)
    resource = Resource.create(attributes={SERVICE_NAME: service_name})
    trace_provider = TracerProvider(sampler=sampler, resource=resource)
    trace.set_tracer_provider(trace_provider)
    
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")  # Configure for Grafana Tempo
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrumentation
    FlaskInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    URLLibInstrumentor().instrument()
    GrpcInstrumentorServer().instrument()

def add_trace_context_to_loguru():
    def enrich_with_trace_info(record):
        print(f"In enrich_with_trace_info")
        span = trace.get_current_span()
        if not span:
            return  # No active span, no action needed

        span_context = span.get_span_context()
        if not span_context:
            return  # No span context available

        if span_context.trace_id != INVALID_TRACE_ID:
            record["extra"]["otel_trace_id"] = f"{span_context.trace_id:032x}"
        else:
            record["extra"]["otel_trace_id"] = None

        if span_context.span_id != INVALID_SPAN_ID:
            record["extra"]["otel_span_id"] = f"{span_context.span_id:016x}"
        else:
            record["extra"]["otel_span_id"] = None

    print(f"In add_trace_context_to_loguru")
    logger.configure(patcher=enrich_with_trace_info)

# Initialize your Flask app
app = Flask(__name__)
logger.add(loki_sink, format="{time} {level} {message}", level="INFO")
# Setup tracing and logging
setup_tracing(service_name="example_service")
add_trace_context_to_loguru()

@app.route("/name/as")
@trace_function("hello")
def hello():
    a = {"name": "niks"}
    logger.info(a)
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
