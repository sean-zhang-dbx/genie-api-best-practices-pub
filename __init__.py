"""
Genie API Client Package

A comprehensive package for interacting with the Databricks Genie API,
featuring robust error handling, exponential backoff, and stress testing capabilities.

Author: Sean Zhang
Version: v0.1
Date: Oct 2025
"""

from .genie_client import GenieClient
from .stress_test import stress_test_api_limit
from .config import (
    DEFAULT_TIMING_CONFIG,
    TIMING_CONFIG_EARLY_BACKOFF,
    TIMING_CONFIG_EARLY_TIMEOUT,
    DEFAULT_STRESS_TEST_PARAMS,
    WORKSPACE_URL,
    PAT,
    SPACE_ID
)

__version__ = "0.1.0"
__author__ = "Sean Zhang"

__all__ = [
    "GenieClient",
    "stress_test_api_limit",
    "DEFAULT_TIMING_CONFIG",
    "TIMING_CONFIG_EARLY_BACKOFF",
    "TIMING_CONFIG_EARLY_TIMEOUT",
    "DEFAULT_STRESS_TEST_PARAMS",
    "WORKSPACE_URL",
    "PAT",
    "SPACE_ID"
]
