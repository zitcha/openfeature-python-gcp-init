from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from openfeature_python_gcp_init.openfeature_setup import (
    Kind,
    LaunchDarklySettings,
    init,
    set_context,
    set_organisation_context,
)


class TestLaunchDarklySettings:
    """Test LaunchDarkly settings configuration."""

    def test_default_settings(self) -> None:
        """Test that LaunchDarkly settings have correct defaults."""
        settings = LaunchDarklySettings()
        assert settings.sdk_key is None
        assert settings.stream is True
        assert settings.poll_interval == 30

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test LaunchDarkly settings load from environment variables."""
        monkeypatch.setenv("LAUNCHDARKLY_SDK_KEY", "test-key")
        monkeypatch.setenv("LAUNCHDARKLY_STREAM", "false")
        monkeypatch.setenv("LAUNCHDARKLY_POLL_INTERVAL", "60")

        settings = LaunchDarklySettings()
        assert settings.sdk_key == "test-key"
        assert settings.stream is False
        assert settings.poll_interval == 60

    def test_invalid_poll_interval_validation(self) -> None:
        """Test validation fails for invalid poll interval."""
        with pytest.raises(ValidationError):
            LaunchDarklySettings(poll_interval=0)


class TestInit:
    """Test OpenFeature client initialization."""

    @patch("openfeature_python_gcp_init.openfeature_setup.api.get_client")
    def test_init_without_sdk_key_returns_default_client(self, mock_get_client: MagicMock) -> None:
        """Test init returns default client when no SDK key available."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = init()

        assert result == mock_client
        mock_get_client.assert_called_once()

    @patch("openfeature_python_gcp_init.openfeature_setup.api.set_provider")
    @patch("openfeature_python_gcp_init.openfeature_setup.api.get_client")
    @patch("openfeature_python_gcp_init.openfeature_setup.LaunchDarklyProvider")
    def test_init_with_sdk_key_sets_launchdarkly_provider(
        self, mock_provider: MagicMock, mock_get_client: MagicMock, mock_set_provider: MagicMock
    ) -> None:
        """Test init sets LaunchDarkly provider when SDK key provided."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = init(sdk_key="test-key", stream=False, poll_interval=60)

        assert result == mock_client
        mock_provider.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider.return_value)
        mock_get_client.assert_called_once()

    @patch("openfeature_python_gcp_init.openfeature_setup.api.get_client")
    @patch("openfeature_python_gcp_init.openfeature_setup.LaunchDarklyProvider")
    def test_init_with_provider_exception_returns_default_client(
        self, mock_provider: MagicMock, mock_get_client: MagicMock
    ) -> None:
        """Test init returns default client when LaunchDarkly provider fails to initialize."""
        mock_provider.side_effect = Exception("Provider initialization failed")
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = init(sdk_key="test-key")

        assert result == mock_client
        mock_get_client.assert_called_once()


class TestDefaultValueBehavior:
    """Test that OpenFeature returns default values when no LaunchDarkly configuration."""

    def test_client_returns_boolean_defaults_without_launchdarkly(self) -> None:
        """Test that OpenFeature client returns boolean defaults when no LaunchDarkly provider set."""
        # Initialize without SDK key to get default OpenFeature client
        client = init()

        # Test boolean flag evaluations return the provided defaults
        assert client.get_boolean_value("feature-enabled", True) is True
        assert client.get_boolean_value("feature-enabled", False) is False
        assert client.get_boolean_value("new-ui", True) is True
        assert client.get_boolean_value("debug-mode", False) is False

    def test_client_returns_string_defaults_without_launchdarkly(self) -> None:
        """Test that OpenFeature client returns string defaults when no LaunchDarkly provider set."""
        # Initialize without SDK key to get default OpenFeature client
        client = init()

        # Test string flag evaluations return the provided defaults
        assert client.get_string_value("welcome-message", "Hello!") == "Hello!"
        assert client.get_string_value("theme", "dark") == "dark"
        assert client.get_string_value("api-endpoint", "https://api.example.com") == "https://api.example.com"
        assert client.get_string_value("empty-default", "") == ""

    def test_client_returns_number_defaults_without_launchdarkly(self) -> None:
        """Test that OpenFeature client returns number defaults when no LaunchDarkly provider set."""
        # Initialize without SDK key to get default OpenFeature client
        client = init()

        # Test integer flag evaluations return the provided defaults
        assert client.get_integer_value("max-items", 10) == 10
        assert client.get_integer_value("retry-count", 3) == 3
        assert client.get_integer_value("zero-default", 0) == 0

        # Test float flag evaluations return the provided defaults
        assert client.get_float_value("timeout", 30.5) == 30.5

    def test_client_returns_object_defaults_without_launchdarkly(self) -> None:
        """Test that OpenFeature client returns object defaults when no LaunchDarkly provider set."""
        # Initialize without SDK key to get default OpenFeature client
        client = init()

        # Test object flag evaluations return the provided defaults
        default_config = {"enabled": True, "timeout": 30}
        assert client.get_object_value("feature-config", default_config) == default_config

        empty_config = {}
        assert client.get_object_value("empty-config", empty_config) == empty_config

        complex_config = {
            "database": {"host": "localhost", "port": 5432},
            "features": ["feature1", "feature2"],
            "metrics": {"enabled": True, "interval": 60},
        }
        assert client.get_object_value("app-config", complex_config) == complex_config

    def test_environment_variable_isolation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the client works correctly when environment variables are explicitly unset."""
        # Ensure no LaunchDarkly environment variables are set
        monkeypatch.delenv("LAUNCHDARKLY_SDK_KEY", raising=False)
        monkeypatch.delenv("LAUNCHDARKLY_STREAM", raising=False)
        monkeypatch.delenv("LAUNCHDARKLY_POLL_INTERVAL", raising=False)

        # Initialize client
        client = init()

        # Verify it returns defaults for all flag types
        assert client.get_boolean_value("test-flag", True) is True
        assert client.get_string_value("test-flag", "default") == "default"
        assert client.get_integer_value("test-flag", 42) == 42
        assert client.get_object_value("test-flag", {"key": "value"}) == {"key": "value"}


class TestContextMethods:
    """Test context setting methods."""

    @patch("openfeature_python_gcp_init.openfeature_setup.api.set_evaluation_context")
    def test_set_context_merges_context_with_kind(self, mock_set_context: MagicMock) -> None:
        """Test set_context merges context with kind."""
        context = {"feature": "enabled"}
        set_context("user-123", context, Kind.ORGANISATION)

        mock_set_context.assert_called_once()
        eval_context = mock_set_context.call_args[0][0]
        assert eval_context.targeting_key == "user-123"
        assert eval_context.attributes["feature"] == "enabled"
        assert eval_context.attributes["kind"] == Kind.ORGANISATION.value

    @patch("openfeature_python_gcp_init.openfeature_setup.set_context")
    def test_set_organisation_context_calls_set_context(self, mock_set_context: MagicMock) -> None:
        """Test set_organisation_context calls set_context with correct parameters."""
        context = {"foo": "bar"}
        set_organisation_context("org-456", context)
        mock_set_context.assert_called_once_with("org-456", context, Kind.ORGANISATION)

    @patch("openfeature_python_gcp_init.openfeature_setup.set_context")
    def test_set_organisation_context_with_default_context(self, mock_set_context: MagicMock) -> None:
        """Test set_organisation_context with default empty context."""
        set_organisation_context("org-456")
        mock_set_context.assert_called_once_with("org-456", {}, Kind.ORGANISATION)
