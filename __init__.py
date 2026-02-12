"""
Genie API Client Package

A comprehensive package for interacting with the Databricks Genie API,
featuring robust error handling, exponential backoff, and stress testing capabilities.

Two client implementations are available:
  - GenieClient: SDK auth + raw requests (full 429 visibility and custom backoff)
      Recommended for production workloads requiring observability and custom retry logic.
  - GenieClientSDK: Pure SDK (_api.do) with built-in retry handling
      The SDK manages 429 retries using server-guided Retry-After delays.
      Set debug=True to observe retry events in logs.

Author: Sean Zhang
Version: v0.2
Date: Feb 2026
"""

from .genie_client import GenieClient
from .genie_client_sdk import GenieClientSDK
from .stress_test import stress_test_api_limit
from .config import (
    DEFAULT_TIMING_CONFIG,
    TIMING_CONFIG_EARLY_BACKOFF,
    TIMING_CONFIG_EARLY_TIMEOUT,
    DEFAULT_STRESS_TEST_PARAMS,
    SPACE_ID
)

__version__ = "0.2.0"
__author__ = "Sean Zhang"

__all__ = [
    "GenieClient",
    "GenieClientSDK",
    "stress_test_api_limit",
    "DEFAULT_TIMING_CONFIG",
    "TIMING_CONFIG_EARLY_BACKOFF",
    "TIMING_CONFIG_EARLY_TIMEOUT",
    "DEFAULT_STRESS_TEST_PARAMS",
    "SPACE_ID"
]
