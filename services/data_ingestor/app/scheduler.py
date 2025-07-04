"""
Data Ingestor Scheduler - Celery Beat scheduler for periodic data collection and batch
    task sending
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import feedparser
from bs4 import BeautifulSoup
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import and_
from tenacity import retry, stop_after_attempt, wait_exponential

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from services.common.app.db.models import RawArticle
from services.common.app.db.session import create_db_session
from services.common.app.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(service_name="data_ingestor_scheduler")
logger = get_logger("data_ingestor_scheduler")

# RSS Feed sources
RSS_FEEDS = [
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
]


class DataIngestor:
    def __init__(self):
        self.session = create_db_session()
        self.stats = {
            "total_fetched": 0,
            "total_saved": 0,
            "errors": 0,
            "start_time": datetime.utcnow(),
        }

    def __del__(self):
        if hasattr(self, "session"):
            self.session.close()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_rss_feed(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Fetch articles from RSS feed with retry logic.
        """
        try:
            logger.info(f"Fetching RSS feed: {feed_config['name']}")
            feed = feedparser.parse(feed_config["url"])
            if feed.bozo:
                logger.warning(f"RSS feed {feed_config['name']} has parsing issues")
            articles = []
            for entry in feed.entries:
                try:
                    article_text = self.extract_article_content(entry)
                    published_at = self.parse_published_date(entry)
                    article_data = {
                        "source": feed_config["source"],
                        "article_url": entry.link,
                        "headline": entry.title,
                        "article_text": article_text,
                        "published_at": published_at,
                    }
                    articles.append(article_data)
                except Exception as e:
                    logger.error(
                        f"Error processing entry from {feed_config['name']}: {str(e)}"
                    )
                    self.stats["errors"] += 1
                    continue
            self.stats["total_fetched"] += len(articles)
            logger.info(
                f"Successfully fetched {len(articles)} articles from {feed_config['name']}"
            )
            return articles
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_config['name']}: {str(e)}")
            self.stats["errors"] += 1
            raise

    def extract_article_content(self, entry) -> str:
        """
        Extract article content from RSS entry.
        """
        content = ""
        if hasattr(entry, "summary") and entry.summary:
            content = entry.summary
        elif hasattr(entry, "description") and entry.description:
            content = entry.description
        elif hasattr(entry, "content") and entry.content:
            content = entry.content[0].value if entry.content else ""
        if content:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(strip=True)
        return content or entry.title

    def parse_published_date(self, entry) -> datetime:
        """
        Parse published date from RSS entry.
        """
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        else:
            return datetime.utcnow()

    def save_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        Save articles to database, avoiding duplicates.
        """
        saved_count = 0
        for article_data in articles:
            try:
                existing = (
                    self.session.query(RawArticle)
                    .filter(RawArticle.article_url == article_data["article_url"])
                    .first()
                )
                if existing:
                    logger.debug(
                        f"Article already exists: {article_data['article_url']}"
                    )
                    continue
                article = RawArticle(**article_data)
                self.session.add(article)
                saved_count += 1
            except Exception as e:
                logger.error(
                    f"Error saving article {article_data.get('article_url', 'unknown')}: {str(e)}"
                )
                self.stats["errors"] += 1
                try:
                    error_article = RawArticle(**article_data, has_error=True)
                    self.session.add(error_article)
                except Exception:
                    pass
        try:
            self.session.commit()
            self.stats["total_saved"] += saved_count
            logger.info(f"Saved {saved_count} new articles to database")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error committing articles to database: {str(e)}")
            self.stats["errors"] += 1
            raise
        return saved_count


# Initialize Celery
celery_app = Celery("data_ingestor")
celery_app.conf.update(
    broker_url=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    beat_schedule={
        "collect-and-send-batch-every-5-minutes": {
            "task": "services.data_ingestor.app.scheduler.collect_and_send_batch",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
    timezone="UTC",
)


@celery_app.task(name="services.data_ingestor.app.scheduler.collect_and_send_batch", bind=True)
def collect_and_send_batch(self):
    """
    Periodic task to collect RSS data and send batch processing tasks.
    """
    logger.info("Starting periodic data collection and batch task sending")
    try:
        ingestor = DataIngestor()
        total_new_articles = 0
        for feed_config in RSS_FEEDS:
            try:
                articles = ingestor.fetch_rss_feed(feed_config)
                saved_count = ingestor.save_articles(articles)
                total_new_articles += saved_count
            except Exception as e:
                logger.error(f"Error processing feed {feed_config['name']}: {e}")
                continue

        logger.info(f"Total new articles collected: {total_new_articles}")
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
    session = None
    try:
        session = create_db_session()
        unprocessed_articles = (
            session.query(RawArticle)
            .filter(
                and_(RawArticle.is_processed == False, RawArticle.has_error == False)
            )
            .all()
        )
        if not unprocessed_articles:
            logger.info("No unprocessed articles found")
            return

        batch_size = 20
        article_ids = [article.id for article in unprocessed_articles]
        batches_sent = 0
        for i in range(0, len(article_ids), batch_size):
            batch_ids = article_ids[i : i + batch_size]
            try:
                celery_app.send_task(
                    "services.sentiment_processor.app.worker.process_sentiment_batch",
                    args=[batch_ids],
                    queue="sentiment_batch_queue",
                )
                batches_sent += 1
                logger.info(
                    f"Sent batch task for {len(batch_ids)} articles: {batch_ids}"
                )
            except Exception as e:
                logger.error(f"Error sending batch task for articles {batch_ids}: {e}")

        logger.info(
            f"Successfully sent {batches_sent} batch tasks for {len(article_ids)} articles"
        )
    except Exception as e:
        logger.error(f"Error in send_batch_processing_tasks: {e}")
    finally:
        if session:
            session.close()

if __name__ == "__main__":
    logger.info(
        "This script defines Celery Beat tasks and is not meant for direct execution."
    )
    # To run beat: celery -A services.data_ingestor.app.scheduler.celery_app beat --loglevel=info
