# Contributing to Hindsight

Thanks for your interest in contributing to Hindsight!

## Getting Started

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   cd hindsight-api && uv sync
   ```
3. Set up your environment:
   ```bash
   export OPENAI_API_KEY=your-key
   ```

## Development

### Running the API locally

```bash
./scripts/dev/start-api.sh
```

### Running the Control Plane locally

```bash
./scripts/dev/start-control-plane.sh
```

### Running the documentation locally

```bash
./scripts/dev/start-docs.sh
```

### Running tests

```bash
cd hindsight-api
uv run pytest tests/
```

### Code style

- Use Python type hints
- Follow existing code patterns
- Keep functions focused and well-named

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Run tests to ensure nothing breaks
4. Submit a PR with a clear description of changes

## Reporting Issues

Open an issue on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)

## Questions?

Open a discussion on GitHub or reach out to the maintainers.
