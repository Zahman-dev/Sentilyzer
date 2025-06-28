"""Sentiment Processor Service - Batch Processing Worker"""

import os

from services.common.app.logging_config import configure_logging, get_logger
from services.sentiment_processor.app.worker import celery_app

# Configure logging
configure_logging(service_name="sentiment_processor_main")
logger = get_logger("sentiment_processor_main")


def main():
    """Main function to start the Celery worker for sentiment processing.
    This function is kept for legacy purposes and direct execution. The primary
    entry point for Docker is the `celery_worker` service.
    """
    logger.info("Starting sentiment processor worker...")

    # Ensure Redis is available
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        logger.error("REDIS_URL environment variable not set. Exiting.")
        return

    # The worker can be started using the celery_app instance
    # The command-line equivalent is:
    # celery -A services.sentiment_processor.app.worker.celery_app worker --loglevel=info
    try:
        # A simple check to see if we can connect to the broker
        with celery_app.connection() as connection:
            logger.info("Successfully connected to the broker.")

        logger.info(
            "Celery app is configured. The worker should be started via the "
            "'celery_worker' service in docker-compose."
        )
        # In a non-Docker setup, you might run the worker directly:
        # celery_app.worker_main(argv=['worker', '--loglevel=info'])

    except Exception as e:
        logger.error(f"Failed to connect to the broker at {redis_url}: {e}")
        logger.error("Please ensure Redis is running and accessible.", exc_info=True)


if __name__ == "__main__":
    main()
