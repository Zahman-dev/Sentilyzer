import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add common module to path
sys.path.append("/common")

import json

import tweepy
from sqlalchemy.exc import IntegrityError

from app.db.models import RawArticle
from app.db.session import get_database_session
from app.logging_config import configure_logging, get_logger

# Configure logging for the service
configure_logging("twitter_ingestor")
logger = get_logger(__name__)


class TwitterIngestor:
    """
    Twitter data ingestor service.

    This service demonstrates the extensibility of our architecture by adding
    a new data source without modifying existing services.
    """

    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        # For demo purposes, we'll use a mock Twitter client
        # In production, you would initialize the real Twitter API client
        self.twitter_client = None
        self._init_twitter_client()

        # Financial search terms
        self.search_terms = [
            "AAPL stock",
            "Apple earnings",
            "TSLA stock",
            "Tesla earnings",
            "MSFT stock",
            "Microsoft earnings",
            "GOOGL stock",
            "Google earnings",
            "AMZN stock",
            "Amazon earnings",
        ]

    def _init_twitter_client(self):
        """Initialize Twitter API client"""
        try:
            if self.bearer_token:
                # Initialize Twitter API v2 client
                self.twitter_client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    wait_on_rate_limit=True,
                )
                logger.info("Twitter API client initialized successfully")
            else:
                logger.warning("Twitter API credentials not found. Using mock mode.")
                self.twitter_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            self.twitter_client = None

    def _generate_mock_tweets(
        self, search_term: str, count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate mock tweets for demonstration purposes.
        In production, this would be replaced with actual Twitter API calls.
        """
        mock_tweets = []
        current_time = datetime.now(timezone.utc)

        sample_texts = [
            f"Great news for {search_term}! Stock is looking bullish today.",
            f"Concerned about {search_term} after recent market volatility.",
            f"Analysts are optimistic about {search_term} long-term prospects.",
            f"Breaking: {search_term} announces new product launch!",
            f"Market sentiment for {search_term} remains mixed.",
            f"Technical analysis suggests {search_term} is oversold.",
            f"Institutional investors are accumulating {search_term}.",
            f"Earnings report for {search_term} exceeded expectations.",
            f"Regulatory concerns may impact {search_term} growth.",
            f"Strong quarterly results from {search_term} division.",
        ]

        for i in range(count):
            tweet_id = (
                f"mock_tweet_{search_term.replace(' ', '_')}_{i}_{int(time.time())}"
            )
            mock_tweet = {
                "id": tweet_id,
                "text": sample_texts[i % len(sample_texts)],
                "author_id": f"user_{i}",
                "created_at": current_time.isoformat(),
                "public_metrics": {
                    "retweet_count": (i * 10) % 100,
                    "like_count": (i * 25) % 200,
                    "reply_count": (i * 5) % 50,
                },
            }
            mock_tweets.append(mock_tweet)

        return mock_tweets

    def fetch_tweets(
        self, search_term: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch tweets for a given search term.
        Returns mock data if Twitter API is not available.
        """
        try:
            if self.twitter_client:
                # Real Twitter API call
                tweets = self.twitter_client.search_recent_tweets(
                    query=f"{search_term} -is:retweet lang:en",
                    max_results=max_results,
                    tweet_fields=["created_at", "author_id", "public_metrics"],
                )

                if tweets.data:
                    return [
                        {
                            "id": str(tweet.id),
                            "text": tweet.text,
                            "author_id": tweet.author_id,
                            "created_at": tweet.created_at.isoformat(),
                            "public_metrics": tweet.public_metrics,
                        }
                        for tweet in tweets.data
                    ]
                else:
                    logger.info(f"No tweets found for search term: {search_term}")
                    return []
            else:
                # Mock mode
                logger.info(f"Using mock data for search term: {search_term}")
                return self._generate_mock_tweets(search_term, max_results)

        except Exception as e:
            logger.error(f"Error fetching tweets for '{search_term}': {e}")
            # Fallback to mock data
            return self._generate_mock_tweets(search_term, max_results)

    def process_tweet_to_article(
        self, tweet: Dict[str, Any], search_term: str
    ) -> Dict[str, Any]:
        """
        Convert a tweet to our standard article format.
        This maintains compatibility with our existing data model.
        """
        # Create a unique URL for the tweet
        tweet_url = f"https://twitter.com/user/status/{tweet['id']}"

        # Use search term as headline prefix
        headline = f"[Twitter - {search_term}] {tweet['text'][:100]}..."

        # Include engagement metrics in the article text
        metrics = tweet.get("public_metrics", {})
        article_text = f"""
        Tweet: {tweet['text']}

        Engagement Metrics:
        - Likes: {metrics.get('like_count', 0)}
        - Retweets: {metrics.get('retweet_count', 0)}
        - Replies: {metrics.get('reply_count', 0)}

        Search Term: {search_term}
        Author ID: {tweet.get('author_id', 'unknown')}
        """

        return {
            "source": "twitter",
            "article_url": tweet_url,
            "headline": headline,
            "article_text": article_text.strip(),
            "published_at": datetime.fromisoformat(
                tweet["created_at"].replace("Z", "+00:00")
            ),
        }

    def save_articles_to_db(self, articles: List[Dict[str, Any]]) -> int:
        """
        Save articles to the database.
        Returns the number of articles successfully saved.
        """
        saved_count = 0

        with get_database_session() as db:
            for article_data in articles:
                try:
                    # Create RawArticle instance
                    article = RawArticle(
                        source=article_data["source"],
                        article_url=article_data["article_url"],
                        headline=article_data["headline"],
                        article_text=article_data["article_text"],
                        published_at=article_data["published_at"],
                    )

                    db.add(article)
                    db.commit()
                    saved_count += 1
                    logger.info(
                        f"Saved tweet article: {article_data['headline'][:50]}..."
                    )

                except IntegrityError:
                    # Article already exists (duplicate URL)
                    db.rollback()
                    logger.debug(
                        f"Duplicate article skipped: {article_data['article_url']}"
                    )

                except Exception as e:
                    db.rollback()
                    logger.error(f"Error saving article: {e}")

        return saved_count

    async def collect_and_process_tweets(self):
        """
        Main collection and processing method.
        This runs the complete pipeline: fetch -> process -> save
        """
        logger.info("Starting Twitter data collection...")
        total_processed = 0

        for search_term in self.search_terms:
            try:
                logger.info(f"Processing search term: {search_term}")

                # Fetch tweets
                tweets = self.fetch_tweets(search_term, max_results=20)

                if not tweets:
                    logger.info(f"No tweets found for: {search_term}")
                    continue

                # Convert tweets to article format
                articles = []
                for tweet in tweets:
                    try:
                        article = self.process_tweet_to_article(tweet, search_term)
                        articles.append(article)
                    except Exception as e:
                        logger.error(
                            f"Error processing tweet {tweet.get('id', 'unknown')}: {e}"
                        )

                # Save to database
                saved_count = self.save_articles_to_db(articles)
                total_processed += saved_count

                logger.info(
                    f"Processed {len(tweets)} tweets, saved {saved_count} new articles for '{search_term}'"
                )

                # Rate limiting - be nice to Twitter API
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error processing search term '{search_term}': {e}")

        logger.info(
            f"Twitter collection completed. Total new articles: {total_processed}"
        )
        return total_processed


async def main():
    """Main function for the Twitter ingestor service"""
    logger.info("Twitter Ingestor Service starting...")

    ingestor = TwitterIngestor()

    # Run collection once
    await ingestor.collect_and_process_tweets()

    logger.info("Twitter Ingestor Service completed.")


if __name__ == "__main__":
    asyncio.run(main())
