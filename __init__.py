"""
Genie API Client Package

A comprehensive package for interacting with the Databricks Genie API,
featuring robust error handling, exponential backoff, and stress testing capabilities.

Uses the Databricks SDK WorkspaceClient for authentication.

Author: Sean Zhang
Version: v0.2
Date: Feb 2026
"""

from .genie_client import GenieClient
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
    "stress_test_api_limit",
    "DEFAULT_TIMING_CONFIG",
    "TIMING_CONFIG_EARLY_BACKOFF",
    "TIMING_CONFIG_EARLY_TIMEOUT",
    "DEFAULT_STRESS_TEST_PARAMS",
    "SPACE_ID"
]
