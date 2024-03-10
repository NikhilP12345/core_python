from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import SpanContext, INVALID_SPAN_ID, INVALID_TRACE_ID
import requests
from opentelemetry.propagate import inject
import datetime
import json
import time
from opentelemetry import trace, propagate
from loguru import logger

def before_request_hook(span, request_to_be_instrumented):
    # Inject the current trace context into the request headers
    inject(request_to_be_instrumented.headers)


def setup_tracing(app = None, service_name="my_service", sampling_rate=1):
    print(f"In setup_tracing")
    sampler = ParentBasedTraceIdRatio(sampling_rate)
    resource = Resource.create(attributes={SERVICE_NAME: service_name})
    trace_provider = TracerProvider(sampler=sampler, resource=resource)
    trace.set_tracer_provider(trace_provider)
    
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")  # Configure for Grafana Tempo
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrumentation
    if(app):
        FlaskInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument(request_hook=before_request_hook)
    else:
        FlaskInstrumentor().instrument()
        RequestsInstrumentor().instrument()

    URLLibInstrumentor().instrument()
    GrpcInstrumentorServer().instrument()
    CeleryInstrumentor().instrument()

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

