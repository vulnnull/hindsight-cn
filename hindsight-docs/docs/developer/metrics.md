# Metrics

Hindsight exposes Prometheus metrics at `/metrics` for monitoring.

```bash
curl http://localhost:8888/metrics
```

## Available Metrics

### Request Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `hindsight_http_requests_total` | Counter | Total HTTP requests (labels: method, endpoint, status_code) |
| `hindsight_http_request_duration_seconds` | Histogram | Request latency (labels: method, endpoint) |

### Memory Operations

| Metric | Type | Description |
|--------|------|-------------|
| `hindsight_retain_duration_seconds` | Histogram | Retain operation latency |
| `hindsight_retain_items_total` | Counter | Total items retained |
| `hindsight_recall_duration_seconds` | Histogram | Recall operation latency |
| `hindsight_recall_results_count` | Histogram | Number of results per recall |
| `hindsight_reflect_duration_seconds` | Histogram | Reflect operation latency |

### LLM Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `hindsight_llm_requests_total` | Counter | LLM API requests (labels: provider, model, status) |
| `hindsight_llm_request_duration_seconds` | Histogram | LLM request latency |
| `hindsight_llm_tokens_total` | Counter | Tokens consumed (labels: provider, token_type) |

### Database Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `hindsight_db_connections_active` | Gauge | Active database connections |
| `hindsight_db_connections_idle` | Gauge | Idle connections in pool |
| `hindsight_db_query_duration_seconds` | Histogram | Query latency (labels: query_type) |

### Memory Bank Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `hindsight_bank_memory_units_total` | Gauge | Total memories per bank |
| `hindsight_bank_entities_total` | Gauge | Total entities per bank |

## Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'hindsight'
    static_configs:
      - targets: ['localhost:8888']
```
