"""
Genie Client for interacting with the Databricks Genie API.

This module provides a robust client for sending messages to the Genie API,
polling for responses, and handling rate limits with exponential backoff.

Uses the Databricks SDK WorkspaceClient for authentication, supporting
workspace-level auth (notebooks), environment variables, profiles, etc.

Author: Sean Zhang
Version: v0.2
Date: Feb 2026
"""

import time
import random
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd
import uuid
import json
import mlflow

from databricks.sdk import WorkspaceClient


class GenieClient:
    """
    Client for interacting with the Genie API, supporting message sending, polling, and trace logging.

    Authentication is handled by the Databricks SDK WorkspaceClient, which automatically
    picks up credentials from the environment (workspace auth in notebooks, ~/.databrickscfg,
    environment variables, etc.).

    Timing parameters (jitter, delay, polling, etc.) are organized in a timing_config dictionary.
    """

    def __init__(
        self,
        space_id: str,
        client: Optional[WorkspaceClient] = None,
        timing_config: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize the GenieClient.

        Args:
            space_id (str): Genie space identifier.
            client (WorkspaceClient, optional): A pre-configured WorkspaceClient.
                If not provided, a default WorkspaceClient() is created, which
                automatically uses workspace auth (notebooks), env vars, or
                ~/.databrickscfg profiles.
            timing_config (dict, optional): Dictionary of timing parameters. Possible keys:
                - base_delay (float): Base delay for exponential backoff (default: 1.0)
                - max_delay (float): Maximum delay for exponential backoff (default: 60.0)
                - jitter (float): Maximum jitter to add to backoff (default: 1.0)
                - initial_poll_interval (float): Initial polling interval in seconds (default: 7.0)
                - max_poll_wait (float): Maximum total wait time in seconds (default: 600.0)
                - poll_backoff_after (float): Time after which polling interval increases and switches to exponential backoff (default: 120.0)
            **kwargs: Additional keyword arguments (unused).
        """
        self.space_id = space_id
        self._workspace_client = client or WorkspaceClient()
        self._genie = self._workspace_client.genie
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Set timing config with defaults, then update with user values
        default_timing = {
            "base_delay": 1.0,
            "max_delay": 60.0,
            "jitter": 1.0,
            "initial_poll_interval": 7.0,
            "max_poll_wait": 600.0,
            "poll_backoff_after": 120.0
        }
        if timing_config:
            default_timing.update(timing_config)
        self.timing_config = default_timing
        self.trace = []  # For tracing all API events

    def _do(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """
        Make an API call through the SDK's authenticated HTTP client.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g. /api/2.0/genie/spaces/...)
            body: Optional request body dict.

        Returns:
            Parsed JSON response as a dict.
        """
        kwargs = {"headers": self._headers}
        if body is not None:
            kwargs["body"] = body
        return self._genie._api.do(method, path, **kwargs)

    def log_trace(self, **kwargs):
        """Log an event to the trace with timestamp."""
        event = {"timestamp": datetime.now().isoformat()}
        event.update(kwargs)
        self.trace.append(event)

    def get_trace_df(self):
        """Convert trace events to a pandas DataFrame with additional metrics."""
        if not self.trace:
            return pd.DataFrame()

        df = pd.DataFrame(self.trace)

        # Convert complex objects to JSON strings
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)

        # Add timing metrics if we have timestamp and question_id columns
        if 'timestamp' in df.columns and 'question_id' in df.columns:
            df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(['question_id', 'timestamp_dt'])
            df['ms_since_prev_event'] = (
                df.groupby('question_id')['timestamp_dt']
                  .diff()
                  .dt.total_seconds()
                  .mul(1000)
                  .fillna(0)
                  .astype(int)
            )
            df = df.drop(columns=['timestamp_dt'])

        return df

    @mlflow.trace()
    def exponential_backoff(self, attempt: int, base_delay: int):
        """Apply exponential backoff with jitter."""
        delay = min(base_delay * (2 ** attempt), self.timing_config["max_delay"])
        delay += random.uniform(0, self.timing_config["jitter"])
        time.sleep(delay)
        return delay

    def _send_with_retries(self, url: str, content: str, phase_prefix: str, max_retries: int = 10) -> Dict[str, Any]:
        """
        Internal helper: POST content to a Genie URL with retry logic for rate limits.

        Used by both start_conversation and create_message.
        """
        question_id = str(uuid.uuid4())

        for attempt in range(max_retries):
            try:
                resp = self._do("POST", url, body={"content": content})

                self.log_trace(
                    phase=phase_prefix,
                    content=content,
                    status_code=200,
                    question_id=question_id,
                    response_content=resp
                )

                # Response may nest under "conversation"/"message" keys or be flat
                convo = resp.get("conversation", resp)
                msg = resp.get("message", resp)

                conversation_id = convo.get("conversation_id", convo.get("id"))
                message_id = msg.get("message_id", msg.get("id"))

                self.log_trace(
                    phase=f"{phase_prefix}_success",
                    conversation_id=conversation_id,
                    message_id=message_id,
                    status=msg.get("status"),
                    question_id=question_id,
                    message_content=msg.get("content")
                )

                return {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "status": msg.get("status"),
                    "status_code": 200,
                    "question_id": question_id,
                    "message_content": msg.get("content")
                }

            except Exception as e:
                error_str = str(e)

                # Handle rate limiting (429)
                if "429" in error_str or "Too Many Requests" in error_str:
                    self.log_trace(phase=f"{phase_prefix}_rate_limited", attempt=attempt, question_id=question_id)
                    self.exponential_backoff(attempt, self.timing_config["base_delay"])
                    continue

                self.log_trace(phase=f"{phase_prefix}_exception", error=error_str, question_id=question_id)
                return {
                    "error": error_str,
                    "status": "FAIL",
                    "status_code": None,
                    "question_id": question_id
                }

        self.log_trace(phase=f"{phase_prefix}_timeout", question_id=question_id)
        return {
            "error": "Rate limit retries exhausted",
            "status": "TIMEOUT",
            "status_code": None,
            "question_id": question_id
        }

    @mlflow.trace()
    def start_conversation(self, content: str, max_retries: int = 10) -> Dict[str, Any]:
        """Start a new conversation with the Genie API."""
        url = f"/api/2.0/genie/spaces/{self.space_id}/start-conversation"
        return self._send_with_retries(url, content, phase_prefix="start_conversation", max_retries=max_retries)

    @mlflow.trace()
    def create_message(self, conversation_id: str, content: str, max_retries: int = 10) -> Dict[str, Any]:
        """Send a follow-up message in an existing conversation."""
        url = f"/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages"
        return self._send_with_retries(url, content, phase_prefix="create_message", max_retries=max_retries)

    # Backward-compatible alias
    send_message = start_conversation

    @mlflow.trace()
    def get_message(self, conversation_id: str, message_id: str, question_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a message from the Genie API."""
        url = f"/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}"

        try:
            resp = self._do("GET", url)

            self.log_trace(
                phase="get_message",
                conversation_id=conversation_id,
                message_id=message_id,
                status_code=200,
                question_id=question_id,
                response_content=resp
            )

            resp["status_code"] = 200

            self.log_trace(
                phase="get_message_success",
                conversation_id=conversation_id,
                message_id=message_id,
                question_id=question_id,
                message_content=resp.get("content")
            )

            return resp

        except Exception as e:
            error_str = str(e)
            self.log_trace(phase="get_message_exception", error=error_str, question_id=question_id)
            return {
                "error": error_str,
                "status": "FAIL",
                "status_code": None,
                "question_id": question_id
            }

    @mlflow.trace()
    def poll_until_complete(self, conversation_id: str, message_id: str, question_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Poll the Genie API until the message is completed, failed, or times out.
        Uses timing_config for polling/backoff parameters.
        """
        start = time.time()
        interval = self.timing_config["initial_poll_interval"]
        attempt = 0

        while True:
            elapsed = time.time() - start
            m = self.get_message(conversation_id, message_id, question_id=question_id)
            status = m.get("status")

            self.log_trace(
                phase="poll",
                conversation_id=conversation_id,
                message_id=message_id,
                status=status,
                question_id=question_id,
                message_content=m.get("content")
            )

            if status in ("COMPLETED", "FAILED", "CANCELLED"):
                self.log_trace(
                    phase="poll_complete",
                    status=status,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    question_id=question_id,
                    message_content=m.get("content")
                )
                return m

            if elapsed > self.timing_config["max_poll_wait"]:
                self.log_trace(phase="poll_timeout", conversation_id=conversation_id, message_id=message_id, question_id=question_id)
                return {
                    "error": "Timeout waiting for completion",
                    "status": "TIMEOUT",
                    "question_id": question_id
                }

            if elapsed > self.timing_config["poll_backoff_after"]:
                attempt += 1
                self.exponential_backoff(attempt, self.timing_config["initial_poll_interval"])
            else:
                time.sleep(interval)

    @mlflow.trace()
    def ask_question(self, question: str, conversation_id: Optional[str] = None):
        """
        Send a question and poll until completion or failure.

        Args:
            question (str): The natural language question to ask.
            conversation_id (str, optional): If provided, continues an existing
                conversation (follow-up). If None, starts a new conversation.

        Returns:
            Dict with the completed message response, including conversation_id
            that can be passed back for follow-up questions.
        """
        if conversation_id:
            resp = self.create_message(conversation_id, question)
        else:
            resp = self.start_conversation(question)

        resp_conversation_id = resp.get("conversation_id")
        message_id = resp.get("message_id")
        question_id = resp.get("question_id")

        if resp_conversation_id and message_id:
            result = self.poll_until_complete(resp_conversation_id, message_id, question_id=question_id)
        else:
            result = resp

        return result
