"""
Configuration settings for Genie API client and testing.

This module contains configuration constants and presets for different
scenarios and testing environments.

Author: Sean Zhang
Version: v0.1
Date: Oct 2025
"""

# Load environment variables from .env file
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    
    # Look for .env file in the same directory as this config file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded credentials from {env_path}")
    else:
        print(f"No .env file found at {env_path}")
        print("Copy env_template.txt to .env and add your credentials")
        
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
    print("  Or set environment variables manually")

# Get credentials from environment variables (with placeholder fallbacks)
WORKSPACE_URL = os.getenv('DATABRICKS_WORKSPACE_URL')
PAT = os.getenv('DATABRICKS_PAT_TOKEN') 
SPACE_ID = os.getenv('DATABRICKS_GENIE_SPACE_ID')

# Default timing configuration for normal operations
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

# Security validation
import warnings

def validate_config():
    """Validate and warn about configuration security."""
    # Check if still using placeholder values
    if PAT == 'dapi_your_token_here' or len(PAT) < 30:
        warnings.warn(
            "Using placeholder PAT token! Create a .env file with your actual credentials. "
            "Never commit real credentials to version control!",
            UserWarning
        )
    
    if WORKSPACE_URL == 'https://your-workspace.cloud.databricks.com':
        warnings.warn(
            "Using placeholder workspace URL! Update your .env file with your actual workspace URL.",
            UserWarning
        )
        
    if SPACE_ID == 'your_space_id_here' or len(SPACE_ID) < 10:
        warnings.warn(
            "Using placeholder space ID! Update your .env file with your actual Genie space ID.", 
            UserWarning
        )

# Auto-validate on import
validate_config()
