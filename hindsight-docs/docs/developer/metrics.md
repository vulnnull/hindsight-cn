# Metrics

Hindsight exposes Prometheus metrics at `/metrics` for monitoring.

```bash
curl http://localhost:8888/metrics
```

## Available Metrics

### Operation Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hindsight.operation.duration` | Histogram | operation, bank_id, source, budget, max_tokens, success | Duration of operations in seconds |
| `hindsight.operation.total` | Counter | operation, bank_id, source, budget, max_tokens, success | Total number of operations executed |

**Labels:**
- `operation`: Operation type (`retain`, `recall`, `reflect`)
- `bank_id`: Memory bank identifier
- `source`: Where the operation was triggered from (`api`, `reflect`, `internal`)
- `budget`: Budget level if specified (`low`, `mid`, `high`)
- `max_tokens`: Max tokens if specified
- `success`: Whether the operation succeeded (`true`, `false`)

The `source` label allows distinguishing between:
- `api`: Direct API calls from clients
- `reflect`: Internal recall calls made during reflect operations
- `internal`: Other internal operations

### LLM Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hindsight.llm.duration` | Histogram | provider, model, scope, success | Duration of LLM API calls in seconds |
| `hindsight.llm.calls.total` | Counter | provider, model, scope, success | Total number of LLM API calls |
| `hindsight.llm.tokens.input` | Counter | provider, model, scope, success, token_bucket | Input tokens for LLM calls |
| `hindsight.llm.tokens.output` | Counter | provider, model, scope, success, token_bucket | Output tokens from LLM calls |

**Labels:**
- `provider`: LLM provider (`openai`, `anthropic`, `gemini`, `groq`, `ollama`, `lmstudio`)
- `model`: Model name (e.g., `gpt-4`, `claude-3-sonnet`)
- `scope`: What the LLM call is for (`memory`, `reflect`, `entity_observation`, `answer`)
- `success`: Whether the call succeeded (`true`, `false`)
- `token_bucket`: Token count bucket for cardinality control (`0-100`, `100-500`, `500-1k`, `1k-5k`, `5k-10k`, `10k-50k`, `50k+`)

### Histogram Buckets

Custom bucket boundaries are configured for better percentile accuracy:

**Operation Duration Buckets (seconds):**
```
0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 60.0, 120.0
```

**LLM Duration Buckets (seconds):**
```
0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0, 60.0, 120.0
```

## Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'hindsight'
    static_configs:
      - targets: ['localhost:8888']
```

## Example Queries

### Average operation latency by type
```promql
rate(hindsight_operation_duration_sum[5m]) / rate(hindsight_operation_duration_count[5m])
```

### LLM calls per minute by provider
```promql
rate(hindsight_llm_calls_total[1m]) * 60
```

### P95 LLM latency
```promql
histogram_quantile(0.95, rate(hindsight_llm_duration_bucket[5m]))
```

### Total tokens consumed by model
```promql
sum by (model) (hindsight_llm_tokens_input_total + hindsight_llm_tokens_output_total)
```

### Internal vs API recall operations
```promql
sum by (source) (rate(hindsight_operation_total{operation="recall"}[5m]))
```
