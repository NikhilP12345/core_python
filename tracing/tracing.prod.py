import os

import google.cloud.logging as google_cloud_logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler, setup_logging
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import (INVALID_SPAN, INVALID_SPAN_CONTEXT,
                                 get_current_span)


def implement_tracing(app, excluded_urls="", sampling_rate=(1/10)):
    # Instruments Flask
    FlaskInstrumentor().instrument_app(app, excluded_urls=excluded_urls)
    # Instruments requests
    RequestsInstrumentor().instrument()
    # Instruments urllib
    URLLibInstrumentor().instrument()
    # Instruments redis
    RedisInstrumentor().instrument()
    # Instrument GRPC
    GrpcInstrumentorServer().instrument()
    # Determines rate at which traces are sampled
    sampler = ParentBasedTraceIdRatio(sampling_rate)
    trace.set_tracer_provider(TracerProvider(sampler=sampler))	
    cloud_trace_exporter = CloudTraceSpanExporter()
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(cloud_trace_exporter)
    )

class PatchedCloudLoggingHandler(CloudLoggingHandler):
    def emit(self, record):
        message = super(CloudLoggingHandler, self).format(record)

        record_otelSpanID = None
        record_otelTraceID = None
        span = get_current_span()
        if span != INVALID_SPAN:
            ctx = span.get_span_context()
            if ctx != INVALID_SPAN_CONTEXT:
                record_otelSpanID = format(ctx.span_id, "016x")
                record_otelTraceID = format(ctx.trace_id, "032x")


        if record_otelTraceID is not None:
            record_otelTraceID = f"projects/{self.project_id}/traces/" + record_otelTraceID
        if record_otelSpanID is not None:
            record_otelSpanID = f"projects/{self.project_id}/spanId/" + record_otelSpanID

        # send off request
        self.transport.send(
            record,
            message,
            resource=(record._resource or self.resource),
            labels=record._labels,
            trace=record_otelTraceID,
            span_id=record_otelSpanID,
            http_request=record.__dict__.get("http_request", None), #Getting populated in generate_access_logs
            source_location=record._source_location,
        )

def inject_trace_into_logs(service_name):
    google_logging_client = google_cloud_logging.Client()
    handler = PatchedCloudLoggingHandler(google_logging_client, name=os.environ.get('LOG_NAME', service_name))
    setup_logging(handler)

    return google_logging_client