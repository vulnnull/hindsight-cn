"""
LLM wrapper for unified configuration across providers.
"""
import os
import time
import asyncio
from typing import Optional, Any, Dict, List
from openai import AsyncOpenAI, RateLimitError, APIError
import logging

logger = logging.getLogger(__name__)

# Disable httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)


class LLMConfig:
    """Configuration for an LLM provider."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider_env: str = "MEMORY_LLM_PROVIDER",
        api_key_env: str = "MEMORY_LLM_API_KEY",
        base_url_env: str = "MEMORY_LLM_BASE_URL",
        model_env: str = "MEMORY_LLM_MODEL",
    ):
        """
        Initialize LLM configuration.

        Args:
            provider: Provider name ("openai", "groq", "ollama"). If None, reads from provider_env.
            api_key: API key. If None, reads from api_key_env.
            base_url: Base URL. If None, reads from base_url_env.
            model: Model name. If None, reads from model_env.
            provider_env: Environment variable name for provider (default: "MEMORY_LLM_PROVIDER")
            api_key_env: Environment variable name for API key (default: "MEMORY_LLM_API_KEY")
            base_url_env: Environment variable name for base URL (default: "MEMORY_LLM_BASE_URL")
            model_env: Environment variable name for model (default: "MEMORY_LLM_MODEL")
        """
        self.provider = (provider or os.getenv(provider_env, "groq")).lower()
        self.api_key = api_key or os.getenv(api_key_env)
        self.base_url = base_url or os.getenv(base_url_env)
        self.model = model or os.getenv(model_env, "openai/gpt-oss-120b")

        # Validate provider
        if self.provider not in ["openai", "groq", "ollama"]:
            raise ValueError(
                f"Invalid LLM provider: {self.provider}. Must be 'openai', 'groq', or 'ollama'."
            )

        # Set default base URLs
        if not self.base_url:
            if self.provider == "groq":
                self.base_url = "https://api.groq.com/openai/v1"
            elif self.provider == "ollama":
                self.base_url = "http://localhost:11434/v1"

        # Validate API key (not needed for ollama)
        if self.provider != "ollama" and not self.api_key:
            raise ValueError(
                f"API key not found for {self.provider}. Set {api_key_env} environment variable."
            )

        # Create client
        if self.provider == "ollama":
            self.client = AsyncOpenAI(api_key="ollama", base_url=self.base_url)
        elif self.base_url:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

        logger.info(
            f"Initialized LLM: provider={self.provider}, model={self.model}, base_url={self.base_url}"
        )

    async def call(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Any] = None,
        scope: str = "memory",
        max_retries: int = 5,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        **kwargs
    ) -> Any:
        """
        Make an LLM API call with consistent configuration and retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            response_format: Optional Pydantic model for structured output
            scope: Scope identifier (e.g., 'memory', 'judge') for future tracking
            max_retries: Maximum number of retry attempts (default: 5)
            initial_backoff: Initial backoff time in seconds (default: 1.0)
            max_backoff: Maximum backoff time in seconds (default: 60.0)
            **kwargs: Additional parameters to pass to the API (temperature, max_tokens, etc.)

        Returns:
            Parsed response if response_format is provided, otherwise the text content

        Raises:
            Exception: Re-raises any API errors after all retries are exhausted
        """
        start_time = time.time()

        call_params = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if response_format is not None:
                    # Use structured output parsing and return .parsed
                    response = await self.client.beta.chat.completions.parse(
                        response_format=response_format,
                        **call_params
                    )
                    result = response.choices[0].message.parsed
                else:
                    # Standard completion and return text content
                    response = await self.client.chat.completions.create(**call_params)
                    result = response.choices[0].message.content

                # Log call details on success
                duration = time.time() - start_time
                usage = response.usage
                logger.info(
                    f"model={self.provider}/{self.model}, "
                    f"input_tokens={usage.prompt_tokens}, output_tokens={usage.completion_tokens}, "
                    f"total_tokens={usage.total_tokens}, time={duration:.3f}s"
                )

                return result

            except RateLimitError as e:
                last_exception = e
                if attempt < max_retries:
                    # Calculate exponential backoff with jitter
                    backoff = min(initial_backoff * (2 ** attempt), max_backoff)
                    # Add jitter (±20%)
                    jitter = backoff * 0.2 * (2 * (time.time() % 1) - 1)
                    sleep_time = backoff + jitter

                    logger.warning(
                        f"Rate limit error (429) on attempt {attempt + 1}/{max_retries + 1}. "
                        f"Retrying in {sleep_time:.2f}s... Error: {str(e)}"
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(
                        f"Rate limit error (429) after {max_retries + 1} attempts. Giving up. Error: {str(e)}"
                    )
                    raise

            except APIError as e:
                last_exception = e
                # Check if it's a retryable error (5xx server errors)
                if hasattr(e, 'status_code') and 500 <= e.status_code < 600:
                    if attempt < max_retries:
                        backoff = min(initial_backoff * (2 ** attempt), max_backoff)
                        jitter = backoff * 0.2 * (2 * (time.time() % 1) - 1)
                        sleep_time = backoff + jitter

                        logger.warning(
                            f"API error ({e.status_code}) on attempt {attempt + 1}/{max_retries + 1}. "
                            f"Retrying in {sleep_time:.2f}s... Error: {str(e)}"
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(
                            f"API error ({e.status_code}) after {max_retries + 1} attempts. Giving up. Error: {str(e)}"
                        )
                        raise
                else:
                    # Non-retryable API error, raise immediately
                    logger.error(f"Non-retryable API error: {str(e)}")
                    raise

            except Exception as e:
                # Any other exception, log and raise immediately
                logger.error(f"Unexpected error during LLM call: {type(e).__name__}: {str(e)}")
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("LLM call failed after all retries with no exception captured")

    @classmethod
    def for_memory(cls) -> "LLMConfig":
        """Create configuration for memory operations."""
        return cls(
            provider_env="MEMORY_LLM_PROVIDER",
            api_key_env="MEMORY_LLM_API_KEY",
            base_url_env="MEMORY_LLM_BASE_URL",
            model_env="MEMORY_LLM_MODEL",
        )

    @classmethod
    def for_judge(cls) -> "LLMConfig":
        """
        Create configuration for judge/evaluator operations.

        Falls back to memory LLM config if judge-specific config not set.
        """
        # Check if judge-specific config exists, otherwise fall back to memory config
        judge_provider = os.getenv("JUDGE_LLM_PROVIDER", os.getenv("MEMORY_LLM_PROVIDER", "groq"))
        judge_api_key = os.getenv("JUDGE_LLM_API_KEY", os.getenv("MEMORY_LLM_API_KEY"))
        judge_base_url = os.getenv("JUDGE_LLM_BASE_URL", os.getenv("MEMORY_LLM_BASE_URL"))
        judge_model = os.getenv("JUDGE_LLM_MODEL", os.getenv("MEMORY_LLM_MODEL", "openai/gpt-oss-120b"))

        return cls(
            provider=judge_provider,
            api_key=judge_api_key,
            base_url=judge_base_url,
            model=judge_model,
            provider_env="JUDGE_LLM_PROVIDER",
            api_key_env="JUDGE_LLM_API_KEY",
            base_url_env="JUDGE_LLM_BASE_URL",
            model_env="JUDGE_LLM_MODEL",
        )
