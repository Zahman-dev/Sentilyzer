"""
Data Ingestor Scheduler - Celery Beat scheduler for periodic data collection and batch
    task sending
"""

import os
from datetime import datetime
from typing import List

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import and_
from sqlalchemy.orm import Session

from services.common.app.db.models import RawArticle, User
from services.common.app.db.session import create_db_session
from services.common.app.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(service_name="data_ingestor_scheduler")
logger = get_logger("data_ingestor_scheduler")


# Initialize Celery
celery_app = Celery("data_ingestor")
celery_app.conf.broker_url = os.environ.get(
    "CELERY_BROKER_URL", "redis://redis:6379/0"
)
celery_app.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    "collect-and-send-batch-every-5-minutes": {
        "task": "services.data_ingestor.app.scheduler.collect_and_send_batch",
        "schedule": 300.0,  # Every 5 minutes
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task
def process_data():
    """Process data from various sources."""
    try:
        logger.info("Starting data processing task")

        # Get database session
        db = create_db_session()

        # Get all active users
        users = db.query(User).filter(User.is_active.is_(True)).all()

        for user in users:
            # Check if user has any articles
            existing_articles = (
                db.query(RawArticle)
                .filter(
                    and_(RawArticle.user_id == user.id, RawArticle.processed.is_(False))
                )
                .all()
            )

            if existing_articles:
                logger.info(
                    "Found {} unprocessed articles for user {}".format(
                        len(existing_articles), user.email
                    )
                )

                # Process articles
                for article in existing_articles:
                    try:
                        # Mark as processed
                        article.processed = True
                        db.commit()

                        logger.info(
                            "Successfully processed article {}".format(article.id)
                        )

                    except Exception as e:
                        logger.error(
                            "Error processing article {}: {}".format(article.id, str(e))
                        )
                        db.rollback()

            else:
                logger.info(
                    "No unprocessed articles found for user {}".format(user.email)
                )

        db.close()
        logger.info("Data processing task completed")

    except Exception as e:
        logger.error("Error in data processing task: {}".format(str(e)))
        if "db" in locals():
            db.close()


@celery_app.task(bind=True)
def collect_and_send_batch(self):
    """
    Periodic task to collect RSS data and send batch processing tasks.

    This task:
    1. Collects data from RSS feeds
    2. Saves new articles to database
    3. Sends batch processing tasks for unprocessed articles
    """
    logger.info("Starting periodic data collection and batch task sending")

    try:
        # Import here to avoid circular imports
        from .main import DataIngestor

        # Create data ingestor instance
        ingestor = DataIngestor()

        # Collect data from all RSS feeds
        total_new_articles = 0
        for feed_config in [
            {
                "name": "reuters_business",
                "url": "https://feeds.reuters.com/reuters/businessNews",
                "source": "reuters",
            },
            {
                "name": "reuters_markets",
                "url": "https://feeds.reuters.com/news/markets",
                "source": "reuters",
            },
            {
                "name": "investing_news",
                "url": "https://www.investing.com/rss/news.rss",
                "source": "investing.com",
            },
        ]:
            try:
                articles = ingestor.fetch_rss_feed(feed_config)
                saved_count = ingestor.save_articles(articles)
                total_new_articles += saved_count
                logger.info(
                    f"Saved {saved_count} new articles from {feed_config['name']}"
                )
            except Exception as e:
                logger.error(f"Error processing feed {feed_config['name']}: {e}")
                continue

        logger.info(f"Total new articles collected: {total_new_articles}")

        # Get all unprocessed articles and send batch tasks
        if total_new_articles > 0:
            send_batch_processing_tasks()

        return {
            "status": "success",
            "new_articles": total_new_articles,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in collect_and_send_batch: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def send_batch_processing_tasks():
    """
    Send batch processing tasks for unprocessed articles.
    """
    try:
        session = create_db_session()

        # Get all unprocessed articles
        unprocessed_articles = (
            session.query(RawArticle)
            .filter(
                and_(RawArticle.is_processed == False, RawArticle.has_error == False)
            )
            .all()
        )

        if not unprocessed_articles:
            logger.info("No unprocessed articles found")
            session.close()
            return

        # Group articles into batches of 20
        batch_size = 20
        article_ids = [article.id for article in unprocessed_articles]

        batches_sent = 0
        for i in range(0, len(article_ids), batch_size):
            batch_ids = article_ids[i : i + batch_size]

            # Send batch task to sentiment processor
            try:
                # Import the task here to avoid circular imports
                from celery import current_app

                # Send task to sentiment processor queue
                current_app.send_task(
                    "app.worker.process_sentiment_batch",
                    args=[batch_ids],
                    queue="sentiment_batch_queue",
                )

                batches_sent += 1
                logger.info(
                    f"Sent batch task for {len(batch_ids)} articles: {batch_ids}"
                )

            except Exception as e:
                logger.error(f"Error sending batch task for articles {batch_ids}: {e}")

        session.close()
        logger.info(
            f"Successfully sent {batches_sent} batch tasks for {len(article_ids)} articles"
        )

    except Exception as e:
        logger.error(f"Error in send_batch_processing_tasks: {e}")


if __name__ == "__main__":
    # This script is intended to be run by Celery Beat, not directly.
    logger.info(
        "This script defines Celery Beat tasks and is not meant for direct execution."
    )
    # To run beat: celery -A services.data_ingestor.app.scheduler.celery_app beat --loglevel=info
