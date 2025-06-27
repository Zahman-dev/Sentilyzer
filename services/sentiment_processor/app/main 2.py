"""
Sentiment Processor Service - Batch Processing Worker
"""

import sys

# Ensure /common is in the path for Docker environment
if "/common" not in sys.path:
    sys.path.insert(0, "/common")

from app.logging_config import configure_logging, get_logger

# Configure logging for the service
configure_logging("sentiment_processor")
logger = get_logger(__name__)


def main():
    """
    Main entry point for sentiment processor service.

    This service now operates as a Celery worker that processes batch sentiment analysis tasks.
    The worker is defined in worker.py and handles:
    1. Receiving batch tasks from Redis queue
    2. Processing multiple articles in batches
    3. Robust error handling with poison pill prevention
    """
    logger.info("Starting Sentiment Processor Service - Batch Processing Mode")

    # Import the worker module to ensure it's loaded
    try:
        from app.worker import celery_app

        logger.info("Worker module loaded successfully")

        # Start the Celery worker
        logger.info("Starting Celery worker for batch sentiment processing...")
        celery_app.worker_main(
            [
                "worker",
                "--loglevel=info",
                "--concurrency=1",  # Single worker to manage memory efficiently
                "--queues=sentiment_batch_queue",
            ]
        )

    except ImportError as e:
        logger.error(f"Failed to import worker module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting worker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
