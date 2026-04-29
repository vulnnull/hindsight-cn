# Changelog

## 0.1.0 (2026-04-28)

- Initial release: `HindsightRuntimeAdapter` for Amazon Bedrock AgentCore Runtime
- `TurnContext` carries runtime session, user, agent, and tenant identifiers across the ephemeral Runtime boundary
- `BankResolver` (with sensible `default_bank_resolver`) maps a `TurnContext` to a stable Hindsight memory bank — durable across Runtime session reprovisioning
- `RetentionPolicy` (off / on, sync vs fire-and-forget) controls whether `run_turn` retains the user/assistant pair after each turn
- `RecallPolicy` (budget, max tokens, prefix) controls memory injection before each turn
- Async `adapter.run_turn(context, payload, agent_callable)` entry point — drop into any AgentCore Runtime handler
- Global `configure(hindsight_api_url, api_key)` helper for shared connection settings
