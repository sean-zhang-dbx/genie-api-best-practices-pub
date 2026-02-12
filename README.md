# Genie API Client Template

A starter Python repo for interacting with the Databricks Genie API, featuring error handling, exponential backoff, and stress testing capabilities. The purpose of this repo is to demonstrate back-off and stress testing, rather than a full end-to-end package to converse with Genie.

**Author:** Sean Zhang  
**Version:** v0.2  
**Date:** Feb 2026

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
from config import SPACE_ID

# Authentication is handled automatically by the Databricks SDK WorkspaceClient
client = GenieClient(space_id=SPACE_ID)

# Ask a question (starts a new conversation)
result = client.ask_question("What is the most common cancer type?")
print(result)

# Follow up in the same conversation
convo_id = result.get("conversation_id")
followup = client.ask_question("Break that down by year", conversation_id=convo_id)
print(followup)

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

3. **Edit `.env` with your Genie space ID:**
   ```bash
   DATABRICKS_GENIE_SPACE_ID=your_actual_space_id
   ```

4. **Authentication:** Handled automatically by the [Databricks SDK](https://databricks-sdk-py.readthedocs.io/en/latest/authentication.html).
   - **In Databricks notebooks:** Workspace auth is automatic.
   - **Locally:** Uses `~/.databrickscfg` profiles or other supported auth methods.

The `.env` file is automatically ignored by git for security.

## Key Features

### GenieClient (`genie_client.py`)
- **SDK Authentication**: Uses `WorkspaceClient` for seamless auth across notebooks and local environments
- **Conversation Follow-ups**: Continue existing conversations with `conversation_id`
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
# - start_conversation(): Start a new conversation with retry attempts
# - create_message(): Follow up in an existing conversation
# - get_message(): Polling for message status
# - poll_until_complete(): Complete polling lifecycle
# - ask_question(): End-to-end question flow

# Custom tracing via logger also available
trace_df = client.get_trace_df()
```

## Security & Best Practices

### Authentication

Authentication is handled by the Databricks SDK `WorkspaceClient`, which supports
multiple methods automatically:

- **Databricks notebooks:** Workspace-level auth (automatic, no configuration needed)
- **Databricks CLI:** Uses `~/.databrickscfg` profiles
- **Environment variables:** `DATABRICKS_HOST` + supported auth methods
- **Azure, AWS, GCP:** Native cloud identity integration

See the [Databricks SDK Authentication docs](https://databricks-sdk-py.readthedocs.io/en/latest/authentication.html) for all options.

### Best Practices

1. **Never commit credentials**: The `.env` file is automatically git-ignored
2. **Monitor rate limits**: Use stress testing to understand your API limits
3. **Configure timeouts**: Adjust `max_poll_wait` based on your use case

## TODOs & Future Enhancements

- [x] Secure credential management with .env files
- [x] SDK-based authentication (WorkspaceClient)
- [x] Conversation follow-up support
- [ ] Develop AI/BI visualizations for log analysis  
- [ ] Implement parsing and retrieval of attachments

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
