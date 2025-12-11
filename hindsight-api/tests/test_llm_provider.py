"""
Test LLM provider with different models and providers.
"""
import os
import pytest
from hindsight_api.engine.llm_wrapper import LLMProvider


# Model matrix: (provider, model)
MODEL_MATRIX = [
    # OpenAI models
    ("openai", "gpt-4o-mini"),
    ("openai", "gpt-5-mini"),
    # Groq models
    ("groq", "llama-3.3-70b-versatile"),
    ("groq", "openai/gpt-oss-120b"),
    # Gemini models
    ("gemini", "gemini-2.0-flash"),
    ("gemini", "gemini-2.5-flash-preview-05-20"),
]


def get_api_key_for_provider(provider: str) -> str | None:
    """Get API key for provider from environment variables."""
    # Try provider-specific env vars first
    provider_key_map = {
        "openai": ["OPENAI_API_KEY", "HINDSIGHT_API_LLM_API_KEY"],
        "groq": ["GROQ_API_KEY", "HINDSIGHT_API_LLM_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "HINDSIGHT_API_LLM_API_KEY"],
    }

    for env_var in provider_key_map.get(provider, []):
        key = os.getenv(env_var)
        if key:
            # For HINDSIGHT_API_LLM_API_KEY, only use if provider matches
            if env_var == "HINDSIGHT_API_LLM_API_KEY":
                configured_provider = os.getenv("HINDSIGHT_API_LLM_PROVIDER", "").lower()
                if configured_provider == provider:
                    return key
            else:
                return key
    return None


@pytest.mark.parametrize("provider,model", MODEL_MATRIX)
@pytest.mark.asyncio
async def test_llm_provider_call(provider: str, model: str):
    """
    Test LLM provider can make a basic call with different models.
    Skips if the required API key is not available.
    """
    api_key = get_api_key_for_provider(provider)
    if not api_key:
        pytest.skip(f"Skipping {provider}/{model}: no API key available")

    llm = LLMProvider(
        provider=provider,
        api_key=api_key,
        base_url="",
        model=model,
    )

    # Test basic call
    response = await llm.call(
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        max_completion_tokens=50,
        temperature=0.1,
    )

    print(f"\n{provider}/{model} response: {response}")
    assert response is not None, f"{provider}/{model} returned None"


@pytest.mark.parametrize("provider,model", MODEL_MATRIX)
@pytest.mark.asyncio
async def test_llm_provider_verify_connection(provider: str, model: str):
    """
    Test LLM provider verify_connection method with different models.
    Skips if the required API key is not available.
    """
    api_key = get_api_key_for_provider(provider)
    if not api_key:
        pytest.skip(f"Skipping {provider}/{model}: no API key available")

    llm = LLMProvider(
        provider=provider,
        api_key=api_key,
        base_url="",
        model=model,
    )

    # Test verify_connection
    await llm.verify_connection()
    print(f"\n{provider}/{model} connection verified")


# Models that support large output (65000+ tokens)
LARGE_OUTPUT_MODELS = [
    ("openai", "gpt-5-mini"),
    ("gemini", "gemini-2.0-flash"),
    ("gemini", "gemini-2.5-flash-preview-05-20"),
]


@pytest.mark.parametrize("provider,model", LARGE_OUTPUT_MODELS)
@pytest.mark.asyncio
async def test_llm_provider_large_output(provider: str, model: str):
    """
    Test LLM provider with large max_completion_tokens (65000).
    Only tests models that support large outputs.
    Skips if the required API key is not available.
    """
    api_key = get_api_key_for_provider(provider)
    if not api_key:
        pytest.skip(f"Skipping {provider}/{model}: no API key available")

    llm = LLMProvider(
        provider=provider,
        api_key=api_key,
        base_url="",
        model=model,
    )

    # Test call with large max_completion_tokens
    response = await llm.call(
        messages=[{"role": "user", "content": "Say 'ok'"}],
        max_completion_tokens=65000,
    )

    print(f"\n{provider}/{model} large output response: {response}")
    assert response is not None, f"{provider}/{model} returned None"
