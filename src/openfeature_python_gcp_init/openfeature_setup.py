import os
from enum import Enum
from typing import Any

from ld_openfeature import LaunchDarklyProvider
from ldclient import Config
from openfeature import api, client
from openfeature.evaluation_context import EvaluationContext


class Kind(Enum):
    ORGANISATION = "organisation"


def init(sdk_key: str = None) -> client.OpenFeatureClient:
    sdk_key = sdk_key or os.getenv("LAUNCHDARKLY_SDK_KEY")
    if not sdk_key:
        raise EnvironmentError("LAUNCHDARKLY_SDK_KEY environment variable is not set")

    provider = LaunchDarklyProvider(Config(sdk_key=sdk_key, stream=False))
    api.set_provider(provider)
    return api.get_client()


def set_organisation_context(id: str, context: dict[str, Any] = {}) -> None:
    set_context(id, context, Kind.ORGANISATION)


def set_context(id: str, context: dict[str, Any], kind: Kind) -> None:
    context = EvaluationContext(id, {**context, "kind": kind})
    api.set_evaluation_context(context)
