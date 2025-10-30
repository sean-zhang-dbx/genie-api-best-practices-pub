"""
Stress testing utilities for the Genie API.

This module provides functions to perform load testing and stress testing
on the Genie API to evaluate performance under various conditions.

Author: Sean Zhang
Version: v0.1
Date: Oct 2025
"""

import threading
import time
import random
import pandas as pd
from datetime import datetime
import mlflow
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .genie_client import GenieClient


def stress_test_api_limit(genie_client: 'GenieClient', question_param: str, num_questions: int, time_frame_s: int) -> pd.DataFrame:
    """
    Sends num_questions in random order within the given time_frame_s (seconds).
    Each question is sent at a random time within the window, then polled for completion.
    Returns a DataFrame of all results.
    Logs the run, parameters, summary metrics, and results artifact to MLflow.
    
    Args:
        genie_client: The GenieClient instance to use for testing
        question_param: The parameter to use in the stress test question, e.g. "cancer type"
        num_questions: Number of questions to send
        time_frame_s: Time window in seconds within which to send all questions
        
    Returns:
        DataFrame containing results from all questions
    """
    print(f"[DEBUG] Using GenieClient timing_config: {getattr(genie_client, 'timing_config', None)}")
    
    with mlflow.start_run(run_name="genie_stress_test"):
        results = []
        start_time = time.time()

        def ask_and_poll(i: int, launch_delay: float):
            """Thread function to ask a question and poll for results."""
            time.sleep(launch_delay)
            question = f"Test question {i+1}: What is the top {i+1} {question_param}?"
            print(f"[ASKING] Question {i+1}/{num_questions}: {question}")
            resp = genie_client.ask_question(question)
            print(f"[RECEIVED] Question {i+1}/{num_questions}: status={resp.get('status')}")
            results.append(resp)

        threads = []
        # Generate random launch delays for each question
        launch_delays = [random.uniform(0, time_frame_s) for _ in range(num_questions)]
        
        # Start threads for each question
        for i in range(num_questions):
            t = threading.Thread(target=ask_and_poll, args=(i, launch_delays[i]))
            t.start()
            threads.append(t)
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        return df