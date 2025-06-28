"""Celery Beat scheduler for periodic data collection and task sending."""

import os
import sys
from datetime import datetime
from typing import Any

import feedparser
from bs4 import BeautifulSoup
from celery import Celery
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
    """A class to handle fetching, parsing, and storing articles from RSS feeds."""

    def __init__(self):
        """Initializes the DataIngestor with a database session and stats."""
        self.session = create_db_session()
        self.stats = {
            "total_fetched": 0,
            "total_saved": 0,
            "errors": 0,
            "start_time": datetime.utcnow(),
        }

    def __del__(self):
        """Ensures the database session is closed when the object is destroyed."""
        if hasattr(self, "session"):
            self.session.close()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_rss_feed(self, feed_config: dict[str, str]) -> list[dict[str, Any]]:
        """Fetch articles from an RSS feed with retry logic."""
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
                        f"Error processing entry from {feed_config['name']}: {e!s}"
                    )
                    self.stats["errors"] += 1
                    continue
            self.stats["total_fetched"] += len(articles)
            logger.info(
                f"Successfully fetched {len(articles)} articles from {feed_config['name']}"
            )
            return articles
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_config['name']}: {e!s}")
            self.stats["errors"] += 1
            raise

    def extract_article_content(self, entry) -> str:
        """Extract article content from an RSS entry."""
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
        """Parse the published date from an RSS entry."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        else:
            return datetime.utcnow()

    def save_articles(self, articles: list[dict[str, Any]]) -> list[int]:
        """Save articles to db, avoid duplicates, and return new article IDs."""
        saved_count = 0
        new_article_ids = []
        articles_to_add = []

        for article_data in articles:
            try:
                existing = (
                    self.session.query(RawArticle.id)
                    .filter(RawArticle.article_url == article_data["article_url"])
                    .first()
                )
                if existing:
                    logger.debug(
                        f"Article already exists: {article_data['article_url']}"
                    )
                    continue
                article = RawArticle(**article_data)
                articles_to_add.append(article)
                saved_count += 1
            except Exception as e:
                logger.error(
                    f"Error preparing article {article_data.get('article_url', 'unknown')} for saving: {e!s}"
                )
                self.stats["errors"] += 1

        if not articles_to_add:
            return []

        try:
            self.session.add_all(articles_to_add)
            self.session.flush()
            new_article_ids = [article.id for article in articles_to_add if article.id]
            self.session.commit()
            self.stats["total_saved"] += saved_count
            logger.info(f"Saved {saved_count} new articles to database.")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error committing new articles to database: {e!s}")
            self.stats["errors"] += len(articles_to_add)
            return []

        return new_article_ids


# Initialize Celery
celery_app = Celery("data_ingestor")
celery_app.conf.update(
    broker_url=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    beat_schedule={
        "collect-and-send-batch-every-5-minutes": {
            "task": "services.data_ingestor.app.tasks.collect_and_send_batch",
            "schedule": 300.0,
        },
    },
    timezone="UTC",
)


@celery_app.task(name="services.data_ingestor.app.tasks.collect_and_send_batch", bind=True)
def collect_and_send_batch(self):
    """Periodically collect RSS data and send batch processing tasks."""
    logger.info("Starting periodic data collection and batch task sending")
    try:
        ingestor = DataIngestor()
        total_new_article_ids = []
        for feed_config in RSS_FEEDS:
            try:
                articles = ingestor.fetch_rss_feed(feed_config)
                if articles:
                    saved_ids = ingestor.save_articles(articles)
                    if saved_ids:
                        total_new_article_ids.extend(saved_ids)
                        logger.info(f"Collected {len(saved_ids)} new article IDs from {feed_config['name']}.")
            except Exception as e:
                logger.error(f"Error processing feed {feed_config['name']}: {e}")
                continue

        if total_new_article_ids:
            logger.info(f"Total new articles to process: {len(total_new_article_ids)}")
            send_batch_processing_task(total_new_article_ids)
        else:
            logger.info("No new articles found in this cycle.")

        return {
            "status": "success",
            "new_articles": len(total_new_article_ids),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error in collect_and_send_batch: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def send_batch_processing_task(article_ids: list[int]):
    """Sends a single, large batch processing task for a list of article IDs."""
    if not article_ids:
        logger.info("No new article IDs to send for processing.")
        return

    try:
        logger.info(f"Sending a single batch task for {len(article_ids)} articles.")
        celery_app.send_task(
            "services.sentiment_processor.app.worker.process_sentiment_batch",
            args=[article_ids],  # Send the entire list as one argument
            queue="sentiment_batch_queue",
        )
        logger.info(
            f"Successfully sent a single batch task for {len(article_ids)} articles."
        )
    except Exception as e:
        logger.error(f"Error sending the batch processing task for articles {article_ids}: {e}")


if __name__ == "__main__":
    logger.info(
        "This script defines Celery Beat tasks and is not meant for direct execution."
    )
