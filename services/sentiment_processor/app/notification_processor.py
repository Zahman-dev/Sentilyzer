"""
Notification Processor - Utility for sending batch tasks to sentiment processor
"""

import os
import sys
import json
import logging
from typing import List

# Add common to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists("/common"):
    common_path = "/common"
else:
    common_path = os.path.join(current_dir, "..", "..", "common")

if common_path not in sys.path:
    sys.path.insert(0, common_path)

from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
celery_app = Celery("notification_sender", broker=REDIS_URL, backend=REDIS_URL)


def send_batch_task(article_ids: List[int]) -> str:
    """
    Send a batch processing task to the sentiment processor.

    Args:
        article_ids: List of article IDs to process

    Returns:
        Task ID
    """
    if not article_ids:
        logger.warning("Empty article_ids list provided")
        return ""

    logger.info(f"Sending batch task for {len(article_ids)} articles: {article_ids}")

    # Import the task from worker
    from app.worker import process_sentiment_batch

    # Send the task
    result = process_sentiment_batch.delay(article_ids)

    logger.info(f"Batch task sent with ID: {result.id}")
    return result.id


if __name__ == "__main__":
    # This module is for utility functions only
    # Use main.py to start the actual worker
    print("Use 'python -m app.main' to start the sentiment processor worker")
