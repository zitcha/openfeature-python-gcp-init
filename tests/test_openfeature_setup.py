from unittest.mock import MagicMock, patch

import pytest
from openfeature.evaluation_context import EvaluationContext
from openfeature_python_gcp_init import openfeature_setup


@pytest.fixture
def sdk_key():
    return "test-sdk-key"


@patch("openfeature.api.set_provider")
@patch("openfeature.api.get_client")
@patch("openfeature_python_gcp_init.openfeature_setup.LaunchDarklyProvider")
@patch("openfeature_python_gcp_init.openfeature_setup.Config")
def test_init_sets_provider_and_returns_api(
    mock_config, mock_provider, mock_get_client, mock_set_provider, sdk_key
):
    mock_get_client.return_value = MagicMock()

    openfeature_setup.init(sdk_key)

    mock_config.assert_called_once_with(sdk_key=sdk_key, stream=False)
    mock_provider.assert_called_once_with(mock_config())
    mock_set_provider.assert_called_once_with(mock_provider())
    mock_get_client.assert_called_once()


@patch("openfeature.api.set_evaluation_context")
def test_set_context_merges_context_with_kind(mock_set_context):
    context = {"feature": "enabled"}
    openfeature_setup.set_context(
        "user-123", context, openfeature_setup.Kind.ORGANISATION
    )

    mock_set_context.assert_called_once()
    eval_context = mock_set_context.call_args[0][0]
    assert isinstance(eval_context, EvaluationContext)
    assert eval_context.targeting_key == "user-123"
    assert eval_context.attributes["feature"] == "enabled"
    assert eval_context.attributes["kind"] == openfeature_setup.Kind.ORGANISATION


@patch("openfeature_python_gcp_init.openfeature_setup.set_context")
def test_set_organisation_context_calls_set_context(mock_set_context):
    context = {"foo": "bar"}
    openfeature_setup.set_organisation_context("org-456", context)
    mock_set_context.assert_called_once_with(
        "org-456", context, openfeature_setup.Kind.ORGANISATION
    )
