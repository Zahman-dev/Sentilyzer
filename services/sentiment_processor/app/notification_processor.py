"""Notification Processor - Utility for sending batch tasks to sentiment processor"""

import os

from celery import Celery

from services.common.app.logging_config import configure_logging, get_logger
from services.sentiment_processor.app.worker import process_sentiment_batch

# Configure logging
configure_logging(service_name="notification_processor")
logger = get_logger("notification_processor")

# Redis configuration to create a Celery app instance
celery_app = Celery("sentilyzer_tasks")
celery_app.conf.update(
    broker_url=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    result_backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
)


def send_sentiment_batch_task(article_ids: list[int]) -> str | None:
    """Sends a batch of article IDs to the Celery queue for sentiment analysis."""
    if not article_ids:
        logger.warning("No article IDs provided to send_sentiment_batch_task.")
        return None

    try:
        task = process_sentiment_batch.signature(
            args=(article_ids,), queue="sentiment_batch_queue"
        )
        logger.info(f"Sending batch task for {len(article_ids)} articles: {article_ids}")
        result = task.apply_async()
        logger.info(f"Task sent with ID: {result.id}")
        return result.id
    except Exception as e:
        logger.error(f"Failed to send task to Celery: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    from services.common.app.db.session import create_db_session

    # This is a sample execution block.
    db = create_db_session()
    if db:
        sample_article_ids = [1, 2, 3]
        task_id = send_sentiment_batch_task(sample_article_ids)
        if task_id:
            logger.info(f"Successfully sent batch task with ID: {task_id}")
        else:
            logger.error("Failed to send batch task.")
        db.close()
    else:
        logger.error("Could not create database session.")

    # This module is for utility functions only
    # Use main.py to start the actual worker
    print("Use 'python -m app.main' to start the sentiment processor worker")
