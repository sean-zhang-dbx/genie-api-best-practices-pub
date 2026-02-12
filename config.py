"""
Configuration settings for Genie API client and testing.

This module contains configuration constants and presets for different
scenarios and testing environments.

Authentication is handled automatically by the Databricks SDK WorkspaceClient
(workspace auth in notebooks, env vars, ~/.databrickscfg profiles, etc.).

Note: The backoff configurations below (base_delay, max_delay, jitter) apply to
429 retry handling in GenieClient (genie_client.py), which uses raw `requests`.
When using GenieClientSDK (genie_client_sdk.py), 429 retries are managed by the
SDK using server-guided Retry-After delays.

Author: Sean Zhang
Version: v0.2
Date: Feb 2026
"""

import os
from pathlib import Path

# Load .env file if it exists (for SPACE_ID and any SDK env vars)
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
    else:
        print(f"No .env file found at {env_path}")
        print("Copy env_template.txt to .env and set DATABRICKS_GENIE_SPACE_ID")

except ImportError:
    pass

# Genie Space ID from environment
SPACE_ID = os.getenv('DATABRICKS_GENIE_SPACE_ID')

# Default timing configuration for normal operations
# Note: base_delay, max_delay, and jitter only apply to 429 retries in GenieClient (raw requests).
# GenieClientSDK's 429 retries are handled by the SDK's retried() decorator (~60s flat delay).
DEFAULT_TIMING_CONFIG = {
    "base_delay": 1.0,              # Base delay for exponential backoff (seconds)
    "max_delay": 60.0,              # Maximum delay for exponential backoff (seconds)
    "jitter": 1.0,                  # Maximum jitter to add to backoff (seconds)
    "initial_poll_interval": 7.0,   # Initial polling interval (seconds)
    "max_poll_wait": 600.0,         # Maximum total wait time (seconds)
    "poll_backoff_after": 120.0     # Time after which polling switches to exponential backoff (seconds)
}

# Configuration for early backoff testing
TIMING_CONFIG_EARLY_BACKOFF = {
    "poll_backoff_after": 5.0,      # Start backoff after 5 seconds
    "initial_poll_interval": 2.0    # Shorter initial polling interval
}

# Configuration for early timeout testing
TIMING_CONFIG_EARLY_TIMEOUT = {
    "max_poll_wait": 5.0,           # Short timeout for testing
    "initial_poll_interval": 2.0    # Shorter initial polling interval
}

# Default stress test parameters
DEFAULT_STRESS_TEST_PARAMS = {
    "num_questions": 10,
    "time_frame_s": 30
}
