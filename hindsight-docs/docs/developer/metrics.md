# Metrics

Hindsight exposes comprehensive metrics for monitoring performance, usage, and system health in production deployments.

## Prometheus Metrics

Hindsight exposes metrics in Prometheus format at the `/metrics` endpoint.

### Accessing Metrics

```bash
# View all metrics
curl http://localhost:8888/metrics

# Scrape with Prometheus
# Add to prometheus.yml:
scrape_configs:
  - job_name: 'hindsight'
    static_configs:
      - targets: ['localhost:8888']
```

## Core Metrics

### Request Metrics

Track API request performance and throughput.

#### `hindsight_http_requests_total`

Total number of HTTP requests by endpoint and status code.

**Type**: Counter
**Labels**:
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: API endpoint path
- `status_code`: HTTP status code (200, 400, 500, etc.)

```promql
# Requests per second by endpoint
rate(hindsight_http_requests_total[5m])

# Error rate (4xx and 5xx)
rate(hindsight_http_requests_total{status_code=~"4..|5.."}[5m])
```

#### `hindsight_http_request_duration_seconds`

HTTP request latency distribution.

**Type**: Histogram
**Labels**:
- `method`: HTTP method
- `endpoint`: API endpoint path

```promql
# P95 latency by endpoint
histogram_quantile(0.95,
  rate(hindsight_http_request_duration_seconds_bucket[5m])
)

# Average request duration
rate(hindsight_http_request_duration_seconds_sum[5m]) /
rate(hindsight_http_request_duration_seconds_count[5m])
```

### Memory Operations

Track retain, recall, and reflect operations.

#### `hindsight_retain_duration_seconds`

Time spent in retain (ingestion) operations.

**Type**: Histogram
**Labels**:
- `bank_id`: Memory bank identifier
- `async`: Whether operation was async (`true`/`false`)

```promql
# P99 retain latency
histogram_quantile(0.99,
  rate(hindsight_retain_duration_seconds_bucket[5m])
)

# Sync vs async retain performance
histogram_quantile(0.50,
  rate(hindsight_retain_duration_seconds_bucket{async="false"}[5m])
)
vs
histogram_quantile(0.50,
  rate(hindsight_retain_duration_seconds_bucket{async="true"}[5m])
)
```

#### `hindsight_retain_items_total`

Total number of memory items retained.

**Type**: Counter
**Labels**:
- `bank_id`: Memory bank identifier

```promql
# Items retained per second
rate(hindsight_retain_items_total[5m])

# Total items retained per bank
sum by(bank_id) (hindsight_retain_items_total)
```

#### `hindsight_recall_duration_seconds`

Time spent in recall (search) operations.

**Type**: Histogram
**Labels**:
- `bank_id`: Memory bank identifier
- `budget`: Thinking budget level (low, mid, high)

```promql
# P95 recall latency by budget
histogram_quantile(0.95,
  rate(hindsight_recall_duration_seconds_bucket[5m])
) by (budget)

# Recall operations per second
rate(hindsight_recall_duration_seconds_count[5m])
```

#### `hindsight_recall_results_count`

Number of results returned by recall operations.

**Type**: Histogram
**Labels**:
- `bank_id`: Memory bank identifier

```promql
# Average number of results per recall
rate(hindsight_recall_results_count_sum[5m]) /
rate(hindsight_recall_results_count_count[5m])
```

#### `hindsight_reflect_duration_seconds`

Time spent in reflect (reasoning) operations.

**Type**: Histogram
**Labels**:
- `bank_id`: Memory bank identifier
- `budget`: Thinking budget level

```promql
# P50, P95, P99 reflect latency
histogram_quantile(0.50, rate(hindsight_reflect_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(hindsight_reflect_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(hindsight_reflect_duration_seconds_bucket[5m]))
```

### LLM Metrics

Track LLM provider usage and performance.

#### `hindsight_llm_requests_total`

Total number of LLM API requests.

**Type**: Counter
**Labels**:
- `provider`: LLM provider (openai, groq, ollama, etc.)
- `model`: Model name
- `operation`: Operation type (fact_extraction, entity_resolution, reasoning, etc.)
- `status`: Request status (success, error, timeout)

```promql
# LLM requests per second by provider
rate(hindsight_llm_requests_total[5m]) by (provider)

# LLM error rate
rate(hindsight_llm_requests_total{status="error"}[5m]) /
rate(hindsight_llm_requests_total[5m])
```

#### `hindsight_llm_request_duration_seconds`

LLM API request latency.

**Type**: Histogram
**Labels**:
- `provider`: LLM provider
- `model`: Model name
- `operation`: Operation type

```promql
# P95 LLM latency by provider
histogram_quantile(0.95,
  rate(hindsight_llm_request_duration_seconds_bucket[5m])
) by (provider)
```

#### `hindsight_llm_tokens_total`

Total tokens consumed (prompt + completion).

**Type**: Counter
**Labels**:
- `provider`: LLM provider
- `model`: Model name
- `token_type`: Token type (prompt, completion)

```promql
# Tokens per second
rate(hindsight_llm_tokens_total[5m])

# Cost estimation (OpenAI GPT-4)
rate(hindsight_llm_tokens_total{provider="openai",model="gpt-4",token_type="prompt"}[5m]) * 0.00003 +
rate(hindsight_llm_tokens_total{provider="openai",model="gpt-4",token_type="completion"}[5m]) * 0.00006
```

### Database Metrics

Track database connection pool and query performance.

#### `hindsight_db_connections_active`

Number of active database connections.

**Type**: Gauge

```promql
# Active connections
hindsight_db_connections_active

# Connection pool utilization %
(hindsight_db_connections_active / 20) * 100
```

#### `hindsight_db_connections_idle`

Number of idle database connections in the pool.

**Type**: Gauge

```promql
# Idle connections
hindsight_db_connections_idle

# Pool efficiency (lower is better)
hindsight_db_connections_idle /
(hindsight_db_connections_active + hindsight_db_connections_idle)
```

#### `hindsight_db_query_duration_seconds`

Database query latency distribution.

**Type**: Histogram
**Labels**:
- `query_type`: Type of query (select, insert, update, vector_search)

```promql
# P95 vector search latency
histogram_quantile(0.95,
  rate(hindsight_db_query_duration_seconds_bucket{query_type="vector_search"}[5m])
)

# Slow queries (> 1s)
histogram_quantile(0.99,
  rate(hindsight_db_query_duration_seconds_bucket[5m])
)
```

### Memory Bank Metrics

Track memory bank usage and statistics.

#### `hindsight_bank_memory_units_total`

Total number of memory units per bank.

**Type**: Gauge
**Labels**:
- `bank_id`: Memory bank identifier
- `fact_type`: Fact type (world, agent, opinion)

```promql
# Total memories per bank
sum by(bank_id) (hindsight_bank_memory_units_total)

# Memory distribution by type
sum by(fact_type) (hindsight_bank_memory_units_total)
```

#### `hindsight_bank_entities_total`

Total number of entities per bank.

**Type**: Gauge
**Labels**:
- `bank_id`: Memory bank identifier

```promql
# Entities per bank
hindsight_bank_entities_total

# Total entities across all banks
sum(hindsight_bank_entities_total)
```

### System Metrics

Track system resource usage.

#### `hindsight_embedding_model_memory_bytes`

Memory used by embedding models.

**Type**: Gauge

```promql
# Model memory in GB
hindsight_embedding_model_memory_bytes / 1024 / 1024 / 1024
```

#### `hindsight_process_cpu_seconds_total`

Total CPU time used by the process.

**Type**: Counter

```promql
# CPU utilization %
rate(hindsight_process_cpu_seconds_total[5m]) * 100
```

#### `hindsight_process_memory_bytes`

Process memory usage.

**Type**: Gauge

```promql
# Memory usage in GB
hindsight_process_memory_bytes / 1024 / 1024 / 1024
```

## Sample Queries

### Performance Monitoring

```promql
# Request latency by endpoint (P95)
histogram_quantile(0.95,
  sum by(endpoint, le) (
    rate(hindsight_http_request_duration_seconds_bucket[5m])
  )
)

# Requests per second
sum(rate(hindsight_http_requests_total[5m]))

# Error rate %
sum(rate(hindsight_http_requests_total{status_code=~"5.."}[5m])) /
sum(rate(hindsight_http_requests_total[5m])) * 100
```

### Capacity Planning

```promql
# Database connection pool saturation
hindsight_db_connections_active / 20 * 100

# LLM request rate trend
rate(hindsight_llm_requests_total[1h])

# Average items retained per operation
rate(hindsight_retain_items_total[5m]) /
rate(hindsight_retain_duration_seconds_count[5m])
```

### Cost Analysis

```promql
# Estimated LLM cost per hour (OpenAI GPT-4)
(
  rate(hindsight_llm_tokens_total{provider="openai",model="gpt-4",token_type="prompt"}[1h]) * 0.00003 +
  rate(hindsight_llm_tokens_total{provider="openai",model="gpt-4",token_type="completion"}[1h]) * 0.00006
) * 3600

# Tokens per operation type
sum by(operation) (
  rate(hindsight_llm_tokens_total[5m])
)
```

### Troubleshooting

```promql
# Slow recalls (> 1 second)
count(
  hindsight_recall_duration_seconds_bucket{le="1.0"} == 0
)

# LLM timeout rate
rate(hindsight_llm_requests_total{status="timeout"}[5m])

# Database connection exhaustion events
changes(hindsight_db_connections_active[5m])
```

## Grafana Dashboard

Example Grafana dashboard configuration:

```json
{
  "dashboard": {
    "title": "Hindsight Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "sum(rate(hindsight_http_requests_total[5m]))"
        }]
      },
      {
        "title": "P95 Latency by Endpoint",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(hindsight_http_request_duration_seconds_bucket[5m])) by (endpoint)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "sum(rate(hindsight_http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(hindsight_http_requests_total[5m])) * 100"
        }]
      },
      {
        "title": "LLM Requests by Provider",
        "targets": [{
          "expr": "sum by(provider) (rate(hindsight_llm_requests_total[5m]))"
        }]
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "hindsight_db_connections_active",
            "legendFormat": "Active"
          },
          {
            "expr": "hindsight_db_connections_idle",
            "legendFormat": "Idle"
          }
        ]
      }
    ]
  }
}
```

## Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: hindsight
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(hindsight_http_requests_total{status_code=~"5.."}[5m])) /
          sum(rate(hindsight_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Slow recalls
      - alert: SlowRecalls
        expr: |
          histogram_quantile(0.95,
            rate(hindsight_recall_duration_seconds_bucket[5m])
          ) > 2.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Recall operations are slow"
          description: "P95 recall latency is {{ $value }}s"

      # Database connection pool exhaustion
      - alert: DatabasePoolExhaustion
        expr: hindsight_db_connections_active / 20 > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Pool utilization is {{ $value | humanizePercentage }}"

      # LLM API failures
      - alert: LLMAPIFailures
        expr: |
          rate(hindsight_llm_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High LLM API error rate"
          description: "LLM error rate: {{ $value }} errors/s"

      # High memory usage
      - alert: HighMemoryUsage
        expr: hindsight_process_memory_bytes / 1024 / 1024 / 1024 > 8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Process using {{ $value }}GB of memory"
```

## Custom Metrics

### Adding Custom Metrics

Extend Hindsight with custom metrics in your application code:

```python
from prometheus_client import Counter, Histogram

# Define custom metric
custom_operations = Counter(
    'hindsight_custom_operations_total',
    'Total custom operations',
    ['operation_type']
)

# Use in code
custom_operations.labels(operation_type='batch_import').inc()
```

## Trace Information

Enable detailed trace information in API responses:

```python
result = client.recall_memories(
    bank_id="my-bank",
    query="test query",
    trace=True  # Enable trace
)

# Access trace data
if result.trace:
    print(f"Total time: {result.trace['total_time']}ms")
    print(f"Activations: {result.trace['activation_count']}")
    print(f"Vector search: {result.trace['vector_search_time']}ms")
    print(f"Reranking: {result.trace['rerank_time']}ms")
```

## Logging Integration

Hindsight logs are structured and can be easily integrated with log aggregation systems:

### JSON Structured Logs

```bash
export HINDSIGHT_API_LOG_FORMAT=json
export HINDSIGHT_API_LOG_LEVEL=info
```

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "hindsight.api",
  "message": "Recall completed",
  "bank_id": "my-bank",
  "query": "test query",
  "results_count": 15,
  "duration_ms": 423
}
```

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for failures

## Best Practices

1. **Set up alerting** for critical metrics (error rate, latency, connection pool)
2. **Monitor costs** by tracking LLM token usage
3. **Track trends** over time to identify capacity needs
4. **Use dashboards** to visualize key metrics
5. **Set appropriate retention** for metrics data (30-90 days)
6. **Correlate metrics** with logs for troubleshooting
7. **Establish baselines** for normal operation
8. **Review metrics regularly** to identify optimization opportunities

---

For metrics-related questions or issues, please [open an issue](https://github.com/your-repo/hindsight/issues) on GitHub.
