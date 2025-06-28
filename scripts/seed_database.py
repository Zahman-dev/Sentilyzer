#!/usr/bin/env python3
"""Database Seeding Script for Sentilyzer Platform.

This script populates the database with sample data for testing purposes.
"""

import os
import random
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "common")
)

from services.common.app.db.models import RawArticle, SentimentScore, User
from services.common.app.db.session import create_db_session

# Sample financial headlines and content
sample_articles = [
    {
        "source": "Reuters",
        "content": (
            "Apple Inc. reported better-than-expected quarterly earnings, "
            "driven by strong iPhone sales and growth in services. "
            "The tech giant's revenue rose 8% to $90.1 billion."
        ),
        "created_at": "2023-05-01T14:30:00",
        "sentiment": ("positive", 0.8),
    },
    {
        "source": "Reuters",
        "content": (
            "Tesla faces production challenges in China market, reporting "
            "lower-than-expected production numbers for the quarter. "
            "Supply chain issues continue to impact manufacturing."
        ),
        "created_at": "2023-05-02T09:15:00",
        "sentiment": ("negative", -0.6),
    },
    {
        "source": "Reuters",
        "content": (
            "Microsoft's cloud business shows strong growth, beating analyst "
            "expectations. Azure revenue increased by 27% year-over-year."
        ),
        "created_at": "2023-05-03T11:45:00",
        "sentiment": ("positive", 0.7),
    },
    {
        "source": "Reuters",
        "content": (
            "Amazon's AWS continues to dominate cloud market, with Q1 revenue "
            "exceeding $21 billion. Growth remains steady at 16%."
        ),
        "created_at": "2023-05-04T16:20:00",
        "sentiment": ("positive", 0.6),
    },
    {
        "source": "Reuters",
        "content": (
            "Meta faces advertising headwinds amid privacy changes and economic "
            "uncertainty. Ad revenue growth slows to 6%."
        ),
        "created_at": "2023-05-05T13:10:00",
        "sentiment": ("negative", -0.3),
    },
]


def create_sample_article(article_data, published_offset_hours):
    """Create a sample article with the given offset from current time."""
    published_at = datetime.utcnow() - timedelta(hours=published_offset_hours)

    return RawArticle(
        source=article_data["source"],
        article_url=f"https://example.com/article_{random.randint(1000, 9999)}",
        headline=article_data["headline"],
        article_text=article_data["content"],
        published_at=published_at,
        is_processed=True,  # Mark as processed so we can add sentiment
    )


def create_sample_sentiment(article_id, sentiment_data):
    """Create a sample sentiment score for an article."""
    label, score = sentiment_data

    return SentimentScore(
        article_id=article_id,
        model_version="placeholder-v1.0",
        sentiment_score=score,
        sentiment_label=label,
    )


def seed_database():
    """Seed the database with sample data."""
    print("🌱 Starting database seeding...")

    session = create_db_session()

    try:
        # Clear existing data
        print("🧹 Clearing existing data...")
        session.query(SentimentScore).delete()
        session.query(RawArticle).delete()
        session.commit()

        # Create test user
        user = User(
            email="test@example.com", is_active=True, created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()

        # Create sample articles
        print("📰 Creating sample articles...")
        articles = []

        for i, article_data in enumerate(sample_articles):
            # Spread articles over the last 48 hours
            offset_hours = i * 6  # Every 6 hours
            article = create_sample_article(article_data, offset_hours)
            session.add(article)
            articles.append((article, article_data["sentiment"]))

        session.commit()

        # Create sentiment scores
        print("📊 Creating sentiment scores...")
        for article, sentiment_data in articles:
            sentiment = create_sample_sentiment(article.id, sentiment_data)
            session.add(sentiment)

        session.commit()

        # Print summary
        total_articles = session.query(RawArticle).count()
        total_sentiments = session.query(SentimentScore).count()

        print("✅ Database seeding completed!")
        print(f"   📰 Articles created: {total_articles}")
        print(f"   📊 Sentiment scores created: {total_sentiments}")
        print("")
        print("🔍 You can now test the API endpoints:")
        print("   GET  http://localhost:8000/health")
        print("   GET  http://localhost:8000/v1/stats")
        print("   GET  http://localhost:8000/v1/sources")
        print("   POST http://localhost:8000/v1/signals")
        print("")
        print("📖 API documentation available at:")
        print("   http://localhost:8000/docs")

    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding database: {e!s}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
