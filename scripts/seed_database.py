#!/usr/bin/env python3
"""
Database Seeding Script for Sentilyzer Platform

This script populates the database with sample data for testing purposes.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "common")
)

from services.common.app.db.session import create_db_session
from services.common.app.db.models import RawArticle, SentimentScore

# Sample financial headlines and content
SAMPLE_ARTICLES = [
    {
        "headline": "Apple Reports Strong Q4 Earnings, Beats Expectations",
        "content": "Apple Inc. reported better-than-expected quarterly earnings, driven by strong iPhone sales and growth in services revenue. The company's stock rose in after-hours trading.",
        "source": "reuters",
        "sentiment": ("positive", 0.8),
    },
    {
        "headline": "Tesla Stock Falls After Production Miss",
        "content": "Tesla shares declined after the electric vehicle maker reported lower-than-expected production numbers for the quarter. Supply chain issues continue to impact manufacturing.",
        "source": "reuters",
        "sentiment": ("negative", -0.6),
    },
    {
        "headline": "Federal Reserve Holds Interest Rates Steady",
        "content": "The Federal Reserve maintained its benchmark interest rate, citing mixed economic signals. Markets showed little reaction to the widely anticipated decision.",
        "source": "investing.com",
        "sentiment": ("neutral", 0.1),
    },
    {
        "headline": "Microsoft Azure Revenue Surges 40% in Cloud Growth",
        "content": "Microsoft's cloud computing division Azure reported 40% revenue growth, outpacing competitor Amazon Web Services. The strong performance boosted Microsoft shares in pre-market trading.",
        "source": "reuters",
        "sentiment": ("positive", 0.7),
    },
    {
        "headline": "Oil Prices Drop on Recession Fears",
        "content": "Crude oil prices fell sharply amid growing concerns about a potential economic recession. Energy stocks were among the worst performers in today's trading session.",
        "source": "investing.com",
        "sentiment": ("negative", -0.5),
    },
    {
        "headline": "Amazon Announces Major Investment in AI Research",
        "content": "Amazon revealed plans to invest billions in artificial intelligence research and development. The initiative aims to enhance the company's cloud services and e-commerce capabilities.",
        "source": "reuters",
        "sentiment": ("positive", 0.6),
    },
    {
        "headline": "Inflation Data Shows Modest Cooling Trend",
        "content": "Latest inflation figures indicate a slight cooling in price pressures, though rates remain above the Federal Reserve's target. Financial markets reacted positively to the news.",
        "source": "investing.com",
        "sentiment": ("positive", 0.4),
    },
    {
        "headline": "Banking Sector Faces Regulatory Scrutiny",
        "content": "Major banks are under increased regulatory scrutiny following recent market volatility. New compliance requirements may impact profitability in the near term.",
        "source": "reuters",
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

        # Create sample articles
        print("📰 Creating sample articles...")
        articles = []

        for i, article_data in enumerate(SAMPLE_ARTICLES):
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

        print(f"✅ Database seeding completed!")
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
        print(f"❌ Error seeding database: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
