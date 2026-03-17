"""Tests for hindsight_hermes.config module."""

from hindsight_hermes.config import (
    HindsightHermesConfig,
    configure,
    get_config,
    reset_config,
)


class TestConfigure:
    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_configure_returns_config(self):
        cfg = configure(hindsight_api_url="http://localhost:8888", api_key="test-key")
        assert isinstance(cfg, HindsightHermesConfig)
        assert cfg.hindsight_api_url == "http://localhost:8888"
        assert cfg.api_key == "test-key"

    def test_configure_defaults(self):
        cfg = configure()
        assert cfg.hindsight_api_url == "https://api.hindsight.vectorize.io"
        assert cfg.api_key is None
        assert cfg.budget == "mid"
        assert cfg.max_tokens == 4096
        assert cfg.tags is None
        assert cfg.recall_tags is None
        assert cfg.recall_tags_match == "any"
        assert cfg.verbose is False

    def test_get_config_returns_none_before_configure(self):
        assert get_config() is None

    def test_get_config_returns_configured(self):
        configure(api_key="k")
        cfg = get_config()
        assert cfg is not None
        assert cfg.api_key == "k"

    def test_reset_config(self):
        configure(api_key="k")
        reset_config()
        assert get_config() is None

    def test_configure_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("HINDSIGHT_API_KEY", "env-key")
        cfg = configure()
        assert cfg.api_key == "env-key"

    def test_explicit_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("HINDSIGHT_API_KEY", "env-key")
        cfg = configure(api_key="explicit-key")
        assert cfg.api_key == "explicit-key"
