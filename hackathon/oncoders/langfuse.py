import base64
import os

import dotenv
import openlit
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


def init_langfuse():
    dotenv.load_dotenv()

    LANGFUSE_AUTH = base64.b64encode(
        f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
        os.environ.get("LANGFUSE_HOST") + "/api/public/otel"
    )
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

    trace_provider = TracerProvider()
    trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))

    # Sets the global default tracer provider
    trace.set_tracer_provider(trace_provider)

    # Creates a tracer from the global tracer provider
    tracer = trace.get_tracer(__name__)
    # Initialize OpenLIT instrumentation. The disable_batch flag is set to true to process traces immediately.
    openlit.init(tracer=tracer, disable_batch=True, disable_metrics=True)

    return tracer
