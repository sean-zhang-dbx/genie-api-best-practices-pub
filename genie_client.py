"""
Genie Client for interacting with the Databricks Genie API.

This module provides a robust client for sending messages to the Genie API,
polling for responses, and handling rate limits with exponential backoff.

Author: Sean Zhang
Version: v0.1
Date: Oct 2025
"""

import time
import random
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd
import uuid
import json
import mlflow


class GenieClient:
    """
    Client for interacting with the Genie API, supporting message sending, polling, and trace logging.
    Timing parameters (jitter, delay, polling, etc.) are organized in a timing_config dictionary.
    """
    
    def __init__(
        self,
        space_id,
        host: Optional[str] = None,
        token: Optional[str] = None,
        timing_config: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize the GenieClient.
        
        Args:
            host (str): Genie API host URL.
            token (str): Personal access token for authentication.
            space_id (str): Genie workspace/space identifier.
            timing_config (dict, optional): Dictionary of timing parameters. Possible keys:
                - base_delay (float): Base delay for exponential backoff (default: 1.0)
                - max_delay (float): Maximum delay for exponential backoff (default: 60.0)
                - jitter (float): Maximum jitter to add to backoff (default: 1.0)
                - initial_poll_interval (float): Initial polling interval in seconds (default: 7.0)
                - max_poll_wait (float): Maximum total wait time in seconds (default: 600.0)
                - poll_backoff_after (float): Time after which polling interval increases and switches to exponential backoff (default: 120.0)
            **kwargs: Additional keyword arguments (unused).
        """
        self.host = host.rstrip("/")
        self.token = token
        self.space_id = space_id
        self.base = f"{self.host}/api/2.0/genie/spaces/{self.space_id}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
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

    @mlflow.trace()
    def send_message(self, content: str, max_retries: int = 10) -> Dict[str, Any]:
        """Send a message to the Genie API with retry logic for rate limits."""
        url = f"{self.base}/start-conversation"
        payload = {"content": content}
        question_id = str(uuid.uuid4())
        
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
                resp_content = None
                
                try:
                    resp_content = resp.json()
                except Exception:
                    resp_content = resp.text
                
                self.log_trace(
                    phase="send_message", 
                    content=content, 
                    status_code=resp.status_code, 
                    question_id=question_id, 
                    response_content=resp_content
                )
                
                if resp.status_code == 200:
                    data = resp_content if isinstance(resp_content, dict) else {}
                    convo = data.get("conversation", {})
                    msg = data.get("message", {})
                    
                    self.log_trace(
                        phase="send_message_success",
                        conversation_id=convo.get("id"),
                        message_id=msg.get("id"),
                        status=msg.get("status"),
                        question_id=question_id,
                        message_content=msg.get("content")
                    )
                    
                    return {
                        "conversation_id": convo.get("id"),
                        "message_id": msg.get("id"),
                        "status": msg.get("status"),
                        "status_code": resp.status_code,
                        "question_id": question_id,
                        "message_content": msg.get("content")
                    }
                
                if resp.status_code == 429:
                    self.log_trace(phase="send_message_rate_limited", attempt=attempt, question_id=question_id)
                    self.exponential_backoff(attempt, self.timing_config["base_delay"])
                    continue
                
                self.log_trace(phase="send_message_error", error=resp.text, status_code=resp.status_code, question_id=question_id)
                return {
                    "error": f"{resp.status_code} {resp.text}", 
                    "status": "FAIL", 
                    "status_code": resp.status_code, 
                    "question_id": question_id
                }
                
            except Exception as e:
                self.log_trace(phase="send_message_exception", error=str(e), question_id=question_id)
                return {
                    "error": str(e), 
                    "status": "FAIL", 
                    "status_code": None, 
                    "question_id": question_id
                }
        
        self.log_trace(phase="send_message_timeout", question_id=question_id)
        return {
            "error": "Rate limit retries exhausted", 
            "status": "TIMEOUT", 
            "status_code": None, 
            "question_id": question_id
        }

    @mlflow.trace()
    def get_message(self, conversation_id: str, message_id: str, question_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a message from the Genie API."""
        url = f"{self.base}/conversations/{conversation_id}/messages/{message_id}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp_content = None
            
            try:
                resp_content = resp.json()
            except Exception:
                resp_content = resp.text
            
            self.log_trace(
                phase="get_message", 
                conversation_id=conversation_id, 
                message_id=message_id, 
                status_code=resp.status_code, 
                question_id=question_id, 
                response_content=resp_content
            )
            
            if resp.status_code == 200:
                result = resp_content if isinstance(resp_content, dict) else {}
                result["status_code"] = resp.status_code
                
                self.log_trace(
                    phase="get_message_success", 
                    conversation_id=conversation_id, 
                    message_id=message_id, 
                    question_id=question_id, 
                    message_content=result.get("content")
                )
                
                return result
            
            self.log_trace(phase="get_message_error", error=resp.text, status_code=resp.status_code, question_id=question_id)
            return {
                "error": f"{resp.status_code} {resp.text}", 
                "status": "FAIL", 
                "status_code": resp.status_code, 
                "question_id": question_id
            }
            
        except Exception as e:
            self.log_trace(phase="get_message_exception", error=str(e), question_id=question_id)
            return {
                "error": str(e), 
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
    def ask_question(self, question: str):
        """Send a question and poll until completion or failure."""
        resp = self.send_message(question)
        conversation_id = resp.get("conversation_id")
        message_id = resp.get("message_id")
        question_id = resp.get("question_id")
        
        if conversation_id and message_id:
            result = self.poll_until_complete(conversation_id, message_id, question_id=question_id)
        else:
            result = resp
            
        return result
