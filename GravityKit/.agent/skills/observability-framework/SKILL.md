---
name: observability-framework
description: "Distributed tracing, structured logging, and metrics framework using OpenTelemetry. Use when setting up full-stack observability for microservices — traces, logs, and metrics with correlation."
user-invocable: true
risk: safe
---

# Observability Framework

Full-stack observability using OpenTelemetry — correlated traces, structured logs, and metrics across distributed systems.

## When to Use
- Setting up distributed tracing across microservices
- Implementing structured logging with trace correlation
- Building the three pillars: metrics + traces + logs
- Integrating with Jaeger, Tempo, Datadog, or Honeycomb

## OpenTelemetry Setup (Node.js)

```bash
npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http @opentelemetry/exporter-metrics-otlp-http
```

```ts
// instrumentation.ts (loaded before app)
import { NodeSDK } from '@opentelemetry/sdk-node'
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'

const sdk = new NodeSDK({
  serviceName: 'my-service',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT
  }),
  instrumentations: [getNodeAutoInstrumentations()]
})
sdk.start()
```

## OpenTelemetry Setup (Python)

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi
```

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)
```

## Custom Spans and Attributes

```ts
const tracer = trace.getTracer('my-service')

async function processOrder(orderId: string) {
  return tracer.startActiveSpan('process-order', async (span) => {
    span.setAttribute('order.id', orderId)
    span.setAttribute('order.source', 'web')
    try {
      const result = await doWork(orderId)
      span.setStatus({ code: SpanStatusCode.OK })
      return result
    } catch (error) {
      span.recordException(error as Error)
      span.setStatus({ code: SpanStatusCode.ERROR })
      throw error
    } finally {
      span.end()
    }
  })
}
```

## Structured Logging with Trace Correlation

```ts
import { trace } from '@opentelemetry/api'
import pino from 'pino'

const logger = pino()

function log(level: string, msg: string, extra?: object) {
  const span = trace.getActiveSpan()
  const ctx = span?.spanContext()
  logger[level]({
    traceId: ctx?.traceId,
    spanId: ctx?.spanId,
    ...extra
  }, msg)
}
```

## Semantic Conventions

Use standard attribute keys for interoperability:

| Concern | Attribute |
|---|---|
| HTTP | `http.method`, `http.route`, `http.status_code` |
| DB | `db.system`, `db.name`, `db.statement` |
| Messaging | `messaging.system`, `messaging.destination` |
| Service | `service.name`, `service.version` |
| Error | `exception.type`, `exception.message` |

## Collector Config (otel-collector.yaml)
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  jaeger:
    endpoint: jaeger:14250
  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
```

## Best Practices
- Always propagate trace context across service boundaries (W3C TraceContext headers)
- Sample at the collector level, not the application level (head-based: 10%, tail-based: errors always)
- Include `service.name`, `service.version`, `deployment.environment` in all spans
- Use span events instead of log statements inside spans
- Keep span names low-cardinality (`GET /users/{id}` not `GET /users/42`)
