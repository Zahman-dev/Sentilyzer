import sys
import os

# This ensures the common library can be found
# For Docker, this path will be /common, for local dev it will be the relative path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "common"))
)

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

import feedparser
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tenacity import retry, stop_after_attempt, wait_exponential
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add common to path - flexible for both Docker and local development
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists("/common"):
    # Docker environment
    common_path = "/common"
else:
    # Local development - go up to services/common
    common_path = os.path.join(current_dir, "..", "..", "common")

if common_path not in sys.path:
    sys.path.insert(0, common_path)

from app.db.session import create_db_session
from app.db.models import RawArticle
from app.schemas.sentiment import RawArticleCreate

# Configure structured JSON logging for production
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Create FastAPI app for health checks
app = FastAPI(title="Data Ingestor Service", version="1.0.0")

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


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        # Test database connectivity
        session = create_db_session()
        session.execute("SELECT 1")
        session.close()

        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "data_ingestor",
            "version": "1.0.0",
            "feeds_configured": len(RSS_FEEDS),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "data_ingestor",
                "error": str(e),
            },
        )


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

            # Parse RSS feed
            feed = feedparser.parse(feed_config["url"])

            if feed.bozo:
                logger.warning(f"RSS feed {feed_config['name']} has parsing issues")

            articles = []
            for entry in feed.entries:
                try:
                    # Extract article content
                    article_text = self.extract_article_content(entry)

                    # Parse published date
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
        # Try different fields for content
        content = ""

        if hasattr(entry, "summary") and entry.summary:
            content = entry.summary
        elif hasattr(entry, "description") and entry.description:
            content = entry.description
        elif hasattr(entry, "content") and entry.content:
            content = entry.content[0].value if entry.content else ""

        # Clean HTML tags
        if content:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(strip=True)

        return content or entry.title  # Fallback to title if no content

    def parse_published_date(self, entry) -> datetime:
        """
        Parse published date from RSS entry.
        """
        # Try different date fields
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        else:
            # Fallback to current time
            return datetime.utcnow()

    def save_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        Save articles to database, avoiding duplicates.
        """
        saved_count = 0

        for article_data in articles:
            try:
                # Check if article already exists
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

                # Create new article
                article = RawArticle(**article_data)
                self.session.add(article)
                saved_count += 1

            except Exception as e:
                logger.error(
                    f"Error saving article {article_data.get('article_url', 'unknown')}: {str(e)}"
                )
                self.stats["errors"] += 1
                # Mark article with error for later investigation
                try:
                    error_article = RawArticle(**article_data, has_error=True)
                    self.session.add(error_article)
                except Exception:
                    pass  # If we can't even save the error record, skip it

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

    async def collect_all_feeds(self):
        """
        Collect articles from all RSS feeds.
        """
        logger.info("Starting RSS feed collection cycle")
        total_saved = 0

        for feed_config in RSS_FEEDS:
            try:
                articles = self.fetch_rss_feed(feed_config)
                saved = self.save_articles(articles)
                total_saved += saved

            except Exception as e:
                logger.error(f"Failed to process feed {feed_config['name']}: {str(e)}")
                self.stats["errors"] += 1
                continue

        # Log periodic statistics
        if self.stats["total_saved"] % 100 == 0 and self.stats["total_saved"] > 0:
            uptime = datetime.utcnow() - self.stats["start_time"]
            logger.info(
                f"Ingestion stats: {self.stats['total_saved']} saved, "
                f"{self.stats['errors']} errors, uptime: {uptime}"
            )

        logger.info(f"Collection cycle completed. Total new articles: {total_saved}")
        return total_saved


async def run_scheduler():
    """
    Run the RSS collection scheduler.
    """
    logger.info("🔄 Starting Data Ingestor Scheduler (Phase 2)")

    ingestor = DataIngestor()
    scheduler = AsyncIOScheduler()

    # Schedule RSS collection every 30 minutes
    scheduler.add_job(
        ingestor.collect_all_feeds,
        "interval",
        minutes=30,
        id="rss_collection",
        name="RSS Feed Collection",
        max_instances=1,
    )

    # Start scheduler
    scheduler.start()
    logger.info("RSS collection scheduler started (every 30 minutes)")

    # Run initial collection
    try:
        await ingestor.collect_all_feeds()
    except Exception as e:
        logger.error(f"Initial RSS collection failed: {str(e)}")

    # Keep the scheduler running
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        scheduler.shutdown()
    finally:
        logger.info("Data ingestor scheduler stopped")


async def main():
    """
    Main function - run both FastAPI server and scheduler.
    """
    import uvicorn

    # Start scheduler in background
    scheduler_task = asyncio.create_task(run_scheduler())

    # Configure and start FastAPI server
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8001, log_level="info")

    server = uvicorn.Server(config)

    try:
        # Run both scheduler and API server
        await asyncio.gather(scheduler_task, server.serve())
    except KeyboardInterrupt:
        logger.info("Shutting down data ingestor service")
    finally:
        scheduler_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
