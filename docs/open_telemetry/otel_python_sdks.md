opentelemetry-sdk: Runtime implementation (Tracer/Meter/Logger providers, samplers, processors, resource). Needed for any real emission.
opentelemetry-exporter-otlp: Convenience layer exposing OTLP exporters; relies on a transport-specific package being installed. Optional; many apps just use the transport package directly.
opentelemetry-instrumentation-fastapi: Auto-instruments FastAPI server spans and attributes.
opentelemetry-instrumentation-requests: Auto-instruments outgoing requests calls.
opentelemetry-instrumentation-logging: Correlates stdlib logging with trace context; optional OTLP log export.
opentelemetry-exporter-otlp-proto-http: Transport-specific OTLP exporter over HTTP (Protobuf payload). Use this for Tempo over HTTP.
opentelemetry-exporter-otlp-proto-common: Shared protobuf/types/utilities used by the HTTP and gRPC exporters. Not a transport; you don’t depend on it directly.