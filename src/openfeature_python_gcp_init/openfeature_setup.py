"""
Module to initialize and configure OpenFeature client with LaunchDarkly provider.
Provides helper functions for setting evaluation context (e.g., organization).
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

from decouple import config
from ld_openfeature import LaunchDarklyProvider
from ldclient import Config
from openfeature import api, client
from openfeature.evaluation_context import EvaluationContext

logger = logging.getLogger(__name__)


class Kind(Enum):
    ORGANISATION = "organisation"


def init(
    sdk_key: Optional[str] = None,
    stream: Optional[bool] = None,
    poll_interval: Optional[int] = None,
) -> client.OpenFeatureClient:
    """
    Initialize the OpenFeature client using LaunchDarkly provider.

    Args:
        sdk_key: LaunchDarkly SDK key; if not provided, read from environment.
        stream: Whether to use streaming mode; if not provided, read from environment.
        poll_interval: Polling interval in seconds; if not provided, read from environment or default to 30.

    Returns:
        Configured OpenFeatureClient instance.
    """
    sdk_key = _config_or_except("LAUNCHDARKLY_SDK_KEY", default=sdk_key, cast=str)
    stream = _config_or_except("LAUNCHDARKLY_STREAM", default=stream, cast=bool)
    poll_interval = _config_or_except("LAUNCHDARKLY_POLL_INTERVAL", default=poll_interval or 30, cast=int)

    logger.info(
        "Initializing LaunchDarklyProvider with sdk_key='%s', stream=%s, poll_interval=%d",
        sdk_key,
        stream,
        poll_interval,
    )

    provider = LaunchDarklyProvider(Config(sdk_key=sdk_key, stream=stream, poll_interval=poll_interval))
    api.set_provider(provider)
    return api.get_client()


def set_organisation_context(id: str, context: Optional[Dict[str, Any]] = None) -> None:
    if context is None:
        context = {}
    set_context(id, context, Kind.ORGANISATION)


def set_context(targeting_key: str, context: Optional[Dict[str, Any]], kind: Kind) -> None:
    """
    Set the global evaluation context for feature flag evaluations.

    Args:
        targeting_key: The unique identifier for targeting.
        context: Additional context attributes.
        kind: The kind of context (e.g., Organisation).
    """
    context = EvaluationContext(targeting_key, {**context, "kind": kind.value})
    api.set_evaluation_context(context)


def _config_or_except(key: str, default: Any, cast: type) -> Any:
    try:
        value = config(key, default=default, cast=cast)
    except Exception:
        value = None
    if value is None:
        raise EnvironmentError(f"Environment variable '{key}' is required but not set")
    return value
