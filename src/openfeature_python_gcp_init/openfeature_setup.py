"""
Module to initialize and configure OpenFeature client with LaunchDarkly provider.
Provides helper functions for setting evaluation context (e.g., organization).
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

from ld_openfeature import LaunchDarklyProvider
from ldclient import Config
from openfeature import api, client
from openfeature.evaluation_context import EvaluationContext
from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Kind(Enum):
    """Context kind enumeration."""

    ORGANISATION = "organisation"


class LaunchDarklySettings(BaseSettings):
    """LaunchDarkly configuration with optional environment variables."""

    sdk_key: Optional[str] = Field(default=None, alias="LAUNCHDARKLY_SDK_KEY", description="LaunchDarkly SDK key")
    stream: bool = Field(default=True, alias="LAUNCHDARKLY_STREAM", description="Enable LaunchDarkly streaming")
    poll_interval: int = Field(
        default=30, alias="LAUNCHDARKLY_POLL_INTERVAL", description="LaunchDarkly polling interval in seconds", gt=0
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


def init(
    sdk_key: Optional[str] = None,
    stream: Optional[bool] = None,
    poll_interval: Optional[int] = None,
) -> client.OpenFeatureClient:
    """
    Initialize OpenFeature client with LaunchDarkly provider when possible.

    Falls back to default OpenFeature client if SDK key is missing.
    The default client will return the provided default values for all feature flag evaluations.

    Args:
        sdk_key: LaunchDarkly SDK key (overrides environment variable)
        stream: Enable streaming (overrides environment variable)
        poll_interval: Polling interval in seconds (overrides environment variable)

    Returns:
        OpenFeature client (with LaunchDarkly provider if SDK key available, default provider otherwise)
    """
    # Load settings from environment with defaults
    settings = LaunchDarklySettings()

    # Override with function parameters if provided
    resolved_sdk_key = sdk_key or settings.sdk_key
    resolved_stream = stream if stream is not None else settings.stream
    resolved_poll_interval = poll_interval if poll_interval is not None else settings.poll_interval

    # Check if SDK key is available
    if not resolved_sdk_key:
        logger.warning(
            "LaunchDarkly SDK key not provided via parameter or LAUNCHDARKLY_SDK_KEY environment variable. "
            "Using default OpenFeature provider that returns feature flag defaults."
        )
        return api.get_client()

    try:
        logger.info(
            "Initializing LaunchDarkly provider with sdk_key='%s...', stream=%s, poll_interval=%d",
            resolved_sdk_key[:8] if len(resolved_sdk_key) > 8 else resolved_sdk_key,
            resolved_stream,
            resolved_poll_interval,
        )

        # Initialize LaunchDarkly provider
        provider = LaunchDarklyProvider(
            Config(sdk_key=resolved_sdk_key, stream=resolved_stream, poll_interval=resolved_poll_interval)
        )
        api.set_provider(provider)

    except Exception as e:
        logger.warning(
            "Failed to initialize LaunchDarkly provider: %s. "
            "Using default OpenFeature provider that returns feature flag defaults.",
            str(e),
        )
        # Don't set any provider, use the default one

    return api.get_client()


def set_organisation_context(id: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Set organization context for feature flag evaluations."""
    if context is None:
        context = {}
    set_context(id, context, Kind.ORGANISATION)


def set_context(targeting_key: str, context: Optional[Dict[str, Any]], kind: Kind) -> None:
    """
    Set the global evaluation context for feature flag evaluations.

    Args:
        targeting_key: The unique identifier for targeting
        context: Additional context attributes
        kind: The kind of context (e.g., Organisation)
    """
    if context is None:
        context = {}
    eval_context = EvaluationContext(targeting_key, {**context, "kind": kind.value})
    api.set_evaluation_context(eval_context)
