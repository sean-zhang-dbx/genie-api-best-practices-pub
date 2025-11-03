# Genie API Client Package

A starter Python repo for interacting with the Databricks Genie API, featuring error handling, exponential backoff, and stress testing capabilities.

**Author:** Sean Zhang  
**Version:** v0.1  
**Date:** Oct 2025

## Package Structure

```
genie-api-best-practices/
├── __init__.py              # Package initialization and exports
├── genie_client.py          # Main GenieClient class
├── stress_test.py           # Stress testing utilities
├── config.py                # Configuration presets and constants
├── genie_api_demo.ipynb     # Demo notebook
├── env_template.txt         # Environment variables template
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules (excludes .env)
└── README.md               # This file
```

## Quick Start

```python
from genie_client import GenieClient
from config import WORKSPACE_URL, PAT, SPACE_ID

# Credentials are automatically loaded from .env file
client = GenieClient(
    space_id=SPACE_ID,
    host=WORKSPACE_URL,
    token=PAT
)

# Ask a question
result = client.ask_question("What is the most common cancer type?")
print(result)

# View trace data
trace_df = client.get_trace_df()
```

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment file:**
   ```bash
   cp env_template.txt .env
   ```

3. **Edit `.env` with your credentials:**
   ```bash
   DATABRICKS_WORKSPACE_URL=https://your-workspace.cloud.databricks.com
   DATABRICKS_PAT_TOKEN=dapi_your_actual_token_here  
   DATABRICKS_GENIE_SPACE_ID=your_actual_space_id
   ```

The `.env` file is automatically ignored by git for security.

## Key Features

### GenieClient (`genie_client.py`)
- **Exponential Backoff**: Automatic retry with exponential backoff and jitter for rate limits (HTTP 429)
- **Configurable Polling**: Customizable polling intervals and timeout behavior
- **MLflow Integration**: Comprehensive tracing of all API interactions

### Stress Testing (`stress_test.py`)
- **Concurrent Testing**: Send multiple questions simultaneously to test rate limits
- **Configuration Benchmarking**: Compare different timing configurations

### Configuration (`config.py`)
- **Predefined Presets**: Multiple timing configurations for different scenarios

## Configuration Options

### Default Timing Configuration Parameters (aligned with [Genie API best practices](https://docs.databricks.com/aws/en/genie/conversation-api#-best-practices-for-using-the-genie-api))

```python
timing_config = {
    "base_delay": 1.0,              # Base delay for exponential backoff (seconds)
    "max_delay": 60.0,              # Maximum delay for exponential backoff (seconds)  
    "jitter": 1.0,                  # Maximum jitter to add to backoff (seconds)
    "initial_poll_interval": 7.0,   # Initial polling interval (seconds) [Best Practices recommendation: between 5-10 seconds]
    "max_poll_wait": 600.0,         # Maximum total wait time (seconds) [Best Practices recommendation: 10 minutes]
    "poll_backoff_after": 120.0     # Time after which polling switches to exponential backoff (seconds) [Best practices recommendation: 2 minutes]
}
```

### Available Presets

- `DEFAULT_TIMING_CONFIG`: Standard production settings
- `TIMING_CONFIG_EARLY_BACKOFF`: Faster backoff for testing
- `TIMING_CONFIG_EARLY_TIMEOUT`: Short timeouts for testing

## Testing & Stress Testing

### Basic Stress Test

```python
from stress_test import stress_test_api_limit

# Run 10 questions over 30 seconds
results = stress_test_api_limit(
    genie_client=client, 
    num_questions=10, 
    time_frame_s=30
)
```

## MLflow Integration

All API interactions are automatically traced with MLflow:

```python
import mlflow

# Traces are automatically logged for:
# - send_message(): Message sending with retry attempts
# - get_message(): Polling for message status
# - poll_until_complete(): Complete polling lifecycle
# - ask_question(): End-to-end question flow

# Custom tracing via logger also available
trace_df = client.get_trace_df()
```

## Security & Best Practices

### Credential Management

The package uses a `.env` file to securely manage credentials:

- **Source code**: Contains only placeholder values (safe to commit)
- **`.env` file**: Contains your actual credentials (git-ignored for security)
- **`env_template.txt`**: Template file showing the required format
- **Automatic loading**: Credentials loaded automatically when importing config

### Security Features

1. **No real credentials in source code**: Only placeholder values are visible in config.py
2. **Git-ignored credentials**: The `.env` file is excluded from version control  
3. **Automatic warnings**: Alerts when using placeholder credentials
4. **Environment fallback**: Works with system environment variables too

### Best Practices

1. **Never commit credentials**: The `.env` file is automatically git-ignored
2. **Use real tokens**: Add your actual Databricks credentials to `.env` file
3. **Rotate tokens regularly**: Set expiration dates on PAT tokens in Databricks
4. **Monitor rate limits**: Use stress testing to understand your API limits
5. **Configure timeouts**: Adjust `max_poll_wait` based on your use case

### Alternative: Environment Variables

Instead of `.env` file, you can set system environment variables:

```bash
export DATABRICKS_WORKSPACE_URL="https://your-workspace.cloud.databricks.com"
export DATABRICKS_PAT_TOKEN="your-pat-token"
export DATABRICKS_GENIE_SPACE_ID="your-space-id"
```

## TODOs & Future Enhancements

- [x] Secure credential management with .env files
- [ ] Develop AI/BI visualizations for log analysis  
- [ ] Implement response-to-conversation features
- [ ] Implement parsing and retrieval of attachments
- [ ] Add workspace-based authentication option

## Currently Out of Scope

- Queuing mechanisms for request management

## Usage Examples

See the `genie_api_demo.ipynb` notebook for comprehensive usage examples including:

- Basic client setup and configuration
- Stress testing demonstrations  
- Early backoff and timeout testing

### Stress Test 
MLflow trace showing exponential backoff 
<img width="1179" height="540" alt="image" src="https://github.com/user-attachments/assets/5ef29a4f-f1a8-4863-9ce5-b31b1a818bdc" />

Custom log trace showing exponential backoff
<img width="1089" height="550" alt="image" src="https://github.com/user-attachments/assets/2e583457-ef78-4701-b98c-42837a91df4b" />


