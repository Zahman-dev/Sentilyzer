#!/usr/bin/env python3
"""
Create test data for Sentilyzer system demonstration.
This script populates the database with sample financial news articles.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.common.app.db.models import RawArticle
from services.common.app.db.session import create_db_session


# Sample financial news articles
SAMPLE_ARTICLES = [
    {
        "headline": "Apple Stock Surges to New Highs on Strong iPhone Sales",
        "article_text": "Apple Inc. shares reached new all-time highs today following reports of exceptional iPhone sales in the latest quarter. The tech giant's strong performance in emerging markets has boosted investor confidence.",
        "ticker": "AAPL",
        "source": "MarketWatch"
    },
    {
        "headline": "Tesla Reports Record Breaking Q4 Deliveries",
        "article_text": "Tesla Inc. announced record-breaking vehicle deliveries for Q4, exceeding analyst expectations. The electric vehicle manufacturer delivered over 500,000 vehicles, marking a significant milestone.",
        "ticker": "TSLA", 
        "source": "Reuters"
    },
    {
        "headline": "Microsoft Azure Revenue Growth Slows, Stock Declines",
        "article_text": "Microsoft Corporation shares fell after the company reported slower growth in its Azure cloud computing division. Revenue growth decelerated to 20% year-over-year, missing analyst forecasts.",
        "ticker": "MSFT",
        "source": "Bloomberg"
    },
    {
        "headline": "Amazon Web Services Faces Increased Competition",
        "article_text": "Amazon.com Inc.'s cloud division AWS is experiencing intensified competition from Google Cloud and Microsoft Azure. Market share data shows AWS losing ground in enterprise customers.",
        "ticker": "AMZN",
        "source": "CNBC"
    },
    {
        "headline": "Google Announces Revolutionary AI Breakthrough",
        "article_text": "Alphabet Inc.'s Google division unveiled a groundbreaking artificial intelligence system that outperforms human capabilities in complex reasoning tasks. The announcement sent shares soaring.",
        "ticker": "GOOGL",
        "source": "TechCrunch"
    },
    {
        "headline": "Meta Platforms Invests Heavily in Metaverse Technology",
        "article_text": "Meta Platforms Inc. announced a $10 billion investment in metaverse infrastructure and virtual reality technologies. CEO Mark Zuckerberg emphasized the long-term potential of the virtual world.",
        "ticker": "META",
        "source": "Wall Street Journal"
    },
    {
        "headline": "NVIDIA Stock Jumps on AI Chip Demand Surge",
        "article_text": "NVIDIA Corporation shares surged following news of unprecedented demand for AI chips from data centers worldwide. The semiconductor company's GPUs are essential for machine learning applications.",
        "ticker": "NVDA",
        "source": "Financial Times"
    },
    {
        "headline": "Netflix Subscriber Growth Disappoints Investors",
        "article_text": "Netflix Inc. reported weaker-than-expected subscriber additions in the latest quarter, leading to a decline in share price. The streaming giant faces increased competition from Disney+ and HBO Max.",
        "ticker": "NFLX",
        "source": "Variety"
    },
    {
        "headline": "PayPal Expands Cryptocurrency Trading Features",
        "article_text": "PayPal Holdings Inc. announced expanded cryptocurrency trading capabilities for its users, allowing buying, selling, and holding of Bitcoin and Ethereum. The move aims to capture the growing crypto market.",
        "ticker": "PYPL",
        "source": "CoinDesk"
    },
    {
        "headline": "Zoom Video Stock Falls on Return-to-Office Trends",
        "article_text": "Zoom Video Communications Inc. shares declined as companies implement return-to-office policies, reducing demand for video conferencing solutions. The company faces challenges in a post-pandemic environment.",
        "ticker": "ZM",
        "source": "Business Insider"
    },
    {
        "headline": "JPMorgan Chase Reports Strong Banking Results",
        "article_text": "JPMorgan Chase & Co. posted strong quarterly results driven by robust lending activity and investment banking fees. The bank's performance reflects a healthy economic environment.",
        "ticker": "JPM",
        "source": "Reuters"
    },
    {
        "headline": "Goldman Sachs Cuts Growth Forecasts Amid Uncertainty",
        "article_text": "Goldman Sachs Group Inc. lowered its economic growth forecasts citing geopolitical tensions and inflation concerns. The investment bank warns of potential market volatility ahead.",
        "ticker": "GS",
        "source": "Bloomberg"
    },
    {
        "headline": "Coca-Cola Reports Steady Growth in Global Markets",
        "article_text": "The Coca-Cola Company demonstrated consistent growth across international markets despite supply chain challenges. The beverage giant's diversified portfolio continues to perform well.",
        "ticker": "KO",
        "source": "MarketWatch"
    },
    {
        "headline": "Johnson & Johnson Faces Legal Challenges Over Drug Pricing",
        "article_text": "Johnson & Johnson confronts mounting legal pressure regarding pharmaceutical pricing practices. The healthcare giant may face significant settlements in ongoing litigation.",
        "ticker": "JNJ",
        "source": "Healthcare Finance"
    },
    {
        "headline": "Bitcoin Price Volatility Affects Crypto-Related Stocks",
        "article_text": "Cryptocurrency market volatility has impacted publicly traded companies with Bitcoin exposure. MicroStrategy and other crypto-holding firms experienced significant share price fluctuations.",
        "ticker": "MSTR",
        "source": "CryptoNews"
    }
]


def create_test_articles() -> None:
    """Create test articles in the database."""
    print("🚀 Creating test data for Sentilyzer system...")
    
    try:
        db = create_db_session()
        
        # Check if we already have test data
        existing_count = db.query(RawArticle).count()
        print(f"📊 Found {existing_count} existing articles in database")
        
        articles_created = 0
        base_time = datetime.utcnow()
        
        for i, article_data in enumerate(SAMPLE_ARTICLES):
            # Create article with staggered timestamps
            published_at = base_time - timedelta(hours=i * 2)
            
            article = RawArticle(
                headline=article_data["headline"],
                article_text=article_data["article_text"],
                article_url=f"https://example.com/article-{i+1}",
                ticker=article_data["ticker"],
                source=article_data["source"],
                published_at=published_at,
                created_at=datetime.utcnow(),
                is_processed=False,
                has_error=False
            )
            
            # Check if article already exists
            existing = db.query(RawArticle).filter(
                RawArticle.headline == article.headline
            ).first()
            
            if not existing:
                db.add(article)
                articles_created += 1
                print(f"✅ Created: {article.headline[:60]}...")
            else:
                print(f"⏭️  Skipped: {article.headline[:60]}... (already exists)")
        
        db.commit()
        
        total_articles = db.query(RawArticle).count()
        print(f"\n🎉 Test data creation complete!")
        print(f"📈 Created {articles_created} new articles")
        print(f"📊 Total articles in database: {total_articles}")
        
        # Show ticker distribution
        print(f"\n📋 Articles by ticker:")
        from sqlalchemy import text
        tickers = db.execute(text("""
            SELECT ticker, COUNT(*) as count 
            FROM raw_articles 
            WHERE ticker IS NOT NULL 
            GROUP BY ticker 
            ORDER BY count DESC
        """)).fetchall()
        
        for ticker, count in tickers:
            print(f"   {ticker}: {count} articles")
            
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()


def trigger_sentiment_processing() -> None:
    """Trigger sentiment processing for the test articles."""
    print("\n🤖 Triggering sentiment analysis for test articles...")
    
    try:
        from services.data_ingestor.app.tasks import collect_and_send_batch
        
        # This will pick up unprocessed articles and send them to sentiment processing
        result = collect_and_send_batch.delay()
        print(f"✅ Sentiment processing task queued: {result.id}")
        
    except Exception as e:
        print(f"❌ Error triggering sentiment processing: {e}")


if __name__ == "__main__":
    print("🧪 Sentilyzer Test Data Creator")
    print("=" * 50)
    
    create_test_articles()
    
    # Ask user if they want to trigger sentiment processing
    response = input("\n🤔 Do you want to trigger sentiment analysis? (y/n): ")
    if response.lower() in ['y', 'yes']:
        trigger_sentiment_processing()
    
    print("\n✨ Done! You can now:")
    print("   1. 🌐 Visit dashboard at: http://localhost:8501")
    print("   2. 🔌 Test API at: http://localhost:8080/docs")
    print("   3. 📊 Check database for processed articles") 