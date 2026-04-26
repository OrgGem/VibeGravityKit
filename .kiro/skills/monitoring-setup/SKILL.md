---
name: monitoring-setup
description: "Set up application monitoring with CloudWatch, Prometheus, and Grafana. Use when instrumenting services, configuring alerts, or building dashboards for production observability."
user-invocable: true
risk: safe
---

# Monitoring Setup

Set up comprehensive monitoring for production services — metrics, alerts, dashboards using CloudWatch, Prometheus, and Grafana.

## When to Use
- Instrumenting a new service with metrics collection
- Setting up Prometheus scraping and Grafana dashboards
- Configuring CloudWatch metrics and alarms for AWS services
- Creating SLO/SLA monitoring and alerting rules

## Prometheus Setup

### Application Instrumentation (Node.js)
```js
const client = require('prom-client')
const register = new client.Registry()
client.collectDefaultMetrics({ register })

const httpDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5]
})
register.registerMetric(httpDuration)

// Express middleware
app.use((req, res, next) => {
  const end = httpDuration.startTimer()
  res.on('finish', () => {
    end({ method: req.method, route: req.route?.path || req.path, status_code: res.statusCode })
  })
  next()
})

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType)
  res.send(await register.metrics())
})
```

### Application Instrumentation (Python)
```python
from prometheus_client import Counter, Histogram, start_http_server

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['endpoint'])

start_http_server(8000)  # Expose /metrics on port 8000
```

### Prometheus Config
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'myapp'
    static_configs:
      - targets: ['myapp:8080']
    metrics_path: /metrics
    scrape_interval: 15s
```

## Alert Rules (Prometheus)
```yaml
# alerts.yml
groups:
  - name: myapp
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.job }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
```

## Grafana Dashboard Panels

### Key Panels to Include
- **Request Rate**: `rate(http_requests_total[5m])`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`
- **P95 Latency**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Active Connections**: `go_goroutines` or `nodejs_active_handles`
- **Memory Usage**: `process_resident_memory_bytes`

## CloudWatch (AWS)
```python
import boto3
cloudwatch = boto3.client('cloudwatch')

# Put custom metric
cloudwatch.put_metric_data(
    Namespace='MyApp/Production',
    MetricData=[{
        'MetricName': 'OrdersProcessed',
        'Value': 42,
        'Unit': 'Count',
        'Dimensions': [{'Name': 'Service', 'Value': 'orders'}]
    }]
)

# Create alarm
cloudwatch.put_metric_alarm(
    AlarmName='HighErrorRate',
    MetricName='5XXError',
    Namespace='AWS/ApplicationELB',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=2,
    Threshold=10,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123:my-topic']
)
```

## Best Practices
- Define SLOs first, then build alerts backward from them
- Use percentiles (P95, P99) for latency, not averages
- Alert on symptoms (user impact), not causes (CPU usage)
- Keep dashboards focused: one row per service, 4-6 panels max
- Test alerts with `amtool` before deploying
