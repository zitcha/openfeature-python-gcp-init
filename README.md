# openfeature-python-gcp-init

A Python package to initialise and configure the OpenFeature client with the LaunchDarkly provider on Google Cloud Platform.

## Features

- Simplified initialisation of the OpenFeature client
- Automatic configuration from environment variables
- Helper functions for setting evaluation contexts (e.g., organisation)

## Installation

```bash
poetry add openfeature-python-gcp-init
```

Or install from source:

```bash
git clone https://github.com/<your-username>/openfeature-python-gcp-init.git
cd openfeature-python-gcp-init
poetry install
```

## Usage

### Bootstrapping

```python
from openfeature_python_gcp_init.openfeature_setup import init, set_organisation_context

# Initialise the OpenFeature client
client = init()

# Set organization context for evaluations
set_organisation_context("org-123", {"name": "Acme Corp"})
```

### Performing feature flag evaluations

Once initialised, you can use the returned client to evaluate feature flags:

```python
# Boolean flag evaluation
new_ui_enabled = client.get_boolean_value("new-ui-enabled", False)
if new_ui_enabled:
    print("Showing new UI")

# String flag evaluation
welcome_message = client.get_string_value("welcome-message", "Welcome!")
print(welcome_message)

# Numeric flag evaluation
max_items = client.get_number_value("max-items", 10)
print(f"Max items allowed: {max_items}")
```

### `init` Parameters

- **sdk_key** (`str`, optional): LaunchDarkly SDK key. If not provided, reads from the `LAUNCHDARKLY_SDK_KEY` environment variable.
- **stream** (`bool`, optional): Enable streaming mode. Reads from `LAUNCHDARKLY_STREAM` if unset.
- **poll_interval** (`int`, optional): Polling interval in seconds. Defaults to 30 or `LAUNCHDARKLY_POLL_INTERVAL`.

## Testing

Run the test suite with:

```bash
poetry run pytest
```
