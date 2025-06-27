"""
Notification Processor - Utility for sending batch tasks to sentiment processor
"""

import os
import sys
from typing import List

# Add common to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../common"))

from celery import Celery

from app.logging_config import configure_logging, get_logger

# Configure logging for the service
configure_logging("notification_processor")
logger = get_logger(__name__)

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
