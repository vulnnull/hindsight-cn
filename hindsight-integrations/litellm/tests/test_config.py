"""Unit tests for hindsight_litellm configuration and defaults."""

import os
from unittest.mock import MagicMock, patch

import pytest

from hindsight_litellm import configure, wrap_openai, wrap_anthropic, reset_config, is_configured
from hindsight_litellm.config import (
    DEFAULT_HINDSIGHT_API_URL,
    DEFAULT_BANK_ID,
    HINDSIGHT_API_KEY_ENV,
    reset_config,
    get_config,
    is_configured,
)
from hindsight_litellm.wrappers import HindsightOpenAI, HindsightAnthropic


class TestDefaults:
    """Test default configuration values."""

    def test_default_api_url(self):
        """Test default API URL is production."""
        assert DEFAULT_HINDSIGHT_API_URL == "https://api.hindsight.vectorize.io"

    def test_default_bank_id(self):
        """Test default bank ID is 'default'."""
        assert DEFAULT_BANK_ID == "default"

    def test_env_var_name(self):
        """Test environment variable name for API key."""
        assert HINDSIGHT_API_KEY_ENV == "HINDSIGHT_API_KEY"


class TestConfigure:
    """Test configure() function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_configure_with_no_arguments(self):
        """Test configure() with no arguments uses defaults."""
        config = configure()

        assert config.hindsight_api_url == DEFAULT_HINDSIGHT_API_URL
        assert config.bank_id == DEFAULT_BANK_ID

    def test_configure_reads_api_key_from_env(self):
        """Test configure() reads API key from environment variable."""
        with patch.dict(os.environ, {HINDSIGHT_API_KEY_ENV: "test-api-key-123"}):
            config = configure()

        assert config.api_key == "test-api-key-123"

    def test_configure_explicit_api_key_overrides_env(self):
        """Test explicit api_key parameter overrides environment variable."""
        with patch.dict(os.environ, {HINDSIGHT_API_KEY_ENV: "env-key"}):
            config = configure(api_key="explicit-key")

        assert config.api_key == "explicit-key"

    def test_configure_explicit_values_override_defaults(self):
        """Test explicit values override defaults."""
        config = configure(
            hindsight_api_url="http://custom-url:8888",
            bank_id="custom-bank",
            api_key="custom-key",
        )

        assert config.hindsight_api_url == "http://custom-url:8888"
        assert config.bank_id == "custom-bank"
        assert config.api_key == "custom-key"

    def test_is_configured_true_with_defaults(self):
        """Test is_configured() returns True with default config."""
        configure()
        assert is_configured() is True

    def test_is_configured_false_when_not_configured(self):
        """Test is_configured() returns False when not configured."""
        reset_config()
        assert is_configured() is False


class TestWrapOpenAI:
    """Test wrap_openai() function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_wrap_openai_with_only_client(self):
        """Test wrap_openai() works with only the client argument."""
        mock_client = MagicMock()

        with patch.dict(os.environ, {HINDSIGHT_API_KEY_ENV: "test-key"}):
            wrapped = wrap_openai(mock_client)

        assert isinstance(wrapped, HindsightOpenAI)
        assert wrapped._bank_id == DEFAULT_BANK_ID
        assert wrapped._api_url == DEFAULT_HINDSIGHT_API_URL
        assert wrapped._api_key == "test-key"

    def test_wrap_openai_uses_defaults(self):
        """Test wrap_openai() uses default values."""
        mock_client = MagicMock()

        wrapped = wrap_openai(mock_client)

        assert wrapped._bank_id == DEFAULT_BANK_ID
        assert wrapped._api_url == DEFAULT_HINDSIGHT_API_URL

    def test_wrap_openai_reads_api_key_from_env(self):
        """Test wrap_openai() reads API key from environment."""
        mock_client = MagicMock()

        with patch.dict(os.environ, {HINDSIGHT_API_KEY_ENV: "env-api-key"}):
            wrapped = wrap_openai(mock_client)

        assert wrapped._api_key == "env-api-key"

    def test_wrap_openai_explicit_overrides_defaults(self):
        """Test wrap_openai() explicit values override defaults."""
        mock_client = MagicMock()

        wrapped = wrap_openai(
            mock_client,
            bank_id="my-bank",
            hindsight_api_url="http://localhost:9999",
            api_key="my-key",
        )

        assert wrapped._bank_id == "my-bank"
        assert wrapped._api_url == "http://localhost:9999"
        assert wrapped._api_key == "my-key"


class TestWrapAnthropic:
    """Test wrap_anthropic() function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_wrap_anthropic_with_only_client(self):
        """Test wrap_anthropic() works with only the client argument."""
        mock_client = MagicMock()

        with patch.dict(os.environ, {HINDSIGHT_API_KEY_ENV: "test-key"}):
            wrapped = wrap_anthropic(mock_client)

        assert isinstance(wrapped, HindsightAnthropic)
        assert wrapped._bank_id == DEFAULT_BANK_ID
        assert wrapped._api_url == DEFAULT_HINDSIGHT_API_URL
        assert wrapped._api_key == "test-key"

    def test_wrap_anthropic_uses_defaults(self):
        """Test wrap_anthropic() uses default values."""
        mock_client = MagicMock()

        wrapped = wrap_anthropic(mock_client)

        assert wrapped._bank_id == DEFAULT_BANK_ID
        assert wrapped._api_url == DEFAULT_HINDSIGHT_API_URL

    def test_wrap_anthropic_reads_api_key_from_env(self):
        """Test wrap_anthropic() reads API key from environment."""
        mock_client = MagicMock()

        with patch.dict(os.environ, {HINDSIGHT_API_KEY_ENV: "env-api-key"}):
            wrapped = wrap_anthropic(mock_client)

        assert wrapped._api_key == "env-api-key"

    def test_wrap_anthropic_explicit_overrides_defaults(self):
        """Test wrap_anthropic() explicit values override defaults."""
        mock_client = MagicMock()

        wrapped = wrap_anthropic(
            mock_client,
            bank_id="my-bank",
            hindsight_api_url="http://localhost:9999",
            api_key="my-key",
        )

        assert wrapped._bank_id == "my-bank"
        assert wrapped._api_url == "http://localhost:9999"
        assert wrapped._api_key == "my-key"
