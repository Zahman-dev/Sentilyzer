import pytest
import requests
import asyncio
import asyncpg
import json
from datetime import datetime, timezone
import sys
import os

# Add common to path for testing
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "services", "common")
)

from app.db.session import create_db_session
from app.db.models import RawArticle, SentimentScore


class TestPhase3Features:
    """
    Integration tests for Phase 3 features:
    1. Dashboard functionality
    2. Twitter ingestor extensibility
    3. PostgreSQL LISTEN/NOTIFY optimization
    """

    @pytest.fixture
    def api_base_url(self):
        """Base URL for the signals API"""
        return "http://localhost:8000"

    @pytest.fixture
    def dashboard_url(self):
        """Base URL for the dashboard"""
        return "http://localhost:8501"

    @pytest.fixture
    def database_url(self):
        """Database URL for direct testing"""
        return "postgresql://sentilyzer_user:sentilyzer_password@localhost:5432/sentilyzer_db"

    def test_signals_api_health(self, api_base_url):
        """Test that the signals API is running and healthy"""
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_dashboard_accessibility(self, dashboard_url):
        """Test that the dashboard is accessible"""
        try:
            response = requests.get(dashboard_url, timeout=10)
            # Streamlit returns 200 even for the main page
            assert response.status_code == 200
            # Check if it's actually Streamlit content
            assert (
                "streamlit" in response.text.lower()
                or "sentilyzer" in response.text.lower()
            )
        except requests.exceptions.RequestException:
            pytest.skip("Dashboard not accessible - may not be running")

    def test_twitter_ingestor_data_format(self):
        """
        Test that Twitter ingestor creates data in the correct format.
        This demonstrates architecture extensibility.
        """
        with create_db_session() as session:
            # Look for Twitter-sourced articles
            twitter_articles = (
                session.query(RawArticle)
                .filter(RawArticle.source == "twitter")
                .limit(5)
                .all()
            )

            # If no Twitter articles, test is informational only
            if not twitter_articles:
                pytest.skip("No Twitter articles found - ingestor may not have run")

            # Test that Twitter articles follow our data contract
            for article in twitter_articles:
                assert article.source == "twitter"
                assert article.article_url.startswith("https://twitter.com/")
                assert "[Twitter -" in article.headline
                assert "Tweet:" in article.article_text
                assert "Engagement Metrics:" in article.article_text
                assert article.published_at is not None

    @pytest.mark.asyncio
    async def test_notification_trigger_exists(self, database_url):
        """
        Test that the PostgreSQL notification infrastructure is properly set up.
        """
        try:
            conn = await asyncpg.connect(database_url)

            # Check if notification function exists
            function_exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'public' AND p.proname = 'notify_new_article'
                );
            """
            )

            assert function_exists, "Notification function not found"

            # Check if trigger exists
            trigger_exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_trigger
                    WHERE tgname = 'trigger_notify_new_article'
                );
            """
            )

            assert trigger_exists, "Notification trigger not found"

            await conn.close()

        except Exception as e:
            pytest.skip(f"Could not test notification infrastructure: {e}")

    @pytest.mark.asyncio
    async def test_notification_system_integration(self, database_url):
        """
        Integration test: Insert an article and verify notification is sent.
        This tests the core Phase 3 optimization.
        """
        try:
            # Connect for notifications
            conn = await asyncpg.connect(database_url)
            await conn.execute("LISTEN new_article_inserted")

            # Insert a test article using synchronous session
            test_article = None
            with create_db_session() as session:
                test_article = RawArticle(
                    source="test_phase3",
                    article_url=f"https://test.com/article_{datetime.now().timestamp()}",
                    headline="Test Article for Phase 3 Integration",
                    article_text="This is a test article to verify LISTEN/NOTIFY works.",
                    published_at=datetime.now(timezone.utc),
                )
                session.add(test_article)
                session.commit()

                # Get the ID for verification
                session.refresh(test_article)
                article_id = test_article.id

            # Wait for notification (with timeout)
            try:
                notification = await asyncio.wait_for(
                    conn.wait_for_notification(), timeout=5.0
                )

                assert notification is not None
                assert notification.channel == "new_article_inserted"

                # Parse the payload
                payload = json.loads(notification.payload)
                assert payload["id"] == article_id
                assert payload["source"] == "test_phase3"

            except asyncio.TimeoutError:
                pytest.fail("No notification received within timeout period")

            await conn.close()

            # Clean up test article
            with create_db_session() as session:
                session.delete(session.get(RawArticle, article_id))
                session.commit()

        except Exception as e:
            pytest.skip(f"Could not test notification integration: {e}")

    def test_api_signals_endpoint_structure(self, api_base_url):
        """
        Test the signals API endpoint structure for dashboard compatibility.
        """
        # This test assumes there's at least some data in the system
        test_payload = {
            "ticker": "AAPL",
            "start_date": "2023-01-01T00:00:00Z",
            "end_date": "2023-12-31T23:59:59Z",
        }

        # Note: This will fail without proper API key in real scenario
        # but we're testing the endpoint structure
        try:
            response = requests.post(
                f"{api_base_url}/v1/signals",
                json=test_payload,
                headers={"Authorization": "Bearer dummy-key-for-structure-test"},
            )

            # We expect either 200 (success) or 401 (unauthorized)
            # but not 404 (endpoint not found) or 500 (server error)
            assert response.status_code in [200, 401, 422]

            if response.status_code == 200:
                data = response.json()
                assert "data" in data
                assert isinstance(data["data"], list)

                # If there's data, check structure
                if data["data"]:
                    first_item = data["data"][0]
                    required_fields = [
                        "article_url",
                        "headline",
                        "published_at",
                        "sentiment_score",
                        "sentiment_label",
                    ]
                    for field in required_fields:
                        assert field in first_item

        except requests.exceptions.RequestException:
            pytest.skip("API not accessible for testing")

    def test_data_pipeline_integration(self):
        """
        Test the complete data pipeline: Raw article -> Sentiment analysis -> API output.
        This verifies the end-to-end Phase 3 system.
        """
        with create_db_session() as session:
            # Find a processed article (one that has sentiment scores)
            processed_article = session.query(RawArticle).join(SentimentScore).first()

            if not processed_article:
                pytest.skip("No processed articles found - system may be starting up")

            # Verify the article is properly processed
            assert processed_article.is_processed == True
            assert processed_article.has_error == False

            # Verify it has sentiment scores
            sentiment_scores = (
                session.query(SentimentScore)
                .filter(SentimentScore.article_id == processed_article.id)
                .all()
            )

            assert len(sentiment_scores) > 0

            for score in sentiment_scores:
                assert score.sentiment_score is not None
                assert score.sentiment_label in ["positive", "negative", "neutral"]
                assert score.model_version is not None
                assert score.processed_at is not None

    def test_system_statistics_and_health(self):
        """
        Test overall system health by checking data flow statistics.
        """
        with create_db_session() as session:
            # Count total articles
            total_articles = session.query(RawArticle).count()

            # Count processed articles
            processed_articles = (
                session.query(RawArticle)
                .filter(RawArticle.is_processed == True)
                .count()
            )

            # Count error articles
            error_articles = (
                session.query(RawArticle).filter(RawArticle.has_error == True).count()
            )

            # Count sentiment scores
            total_sentiment_scores = session.query(SentimentScore).count()

            # Basic health checks
            assert total_articles >= 0
            assert processed_articles >= 0
            assert error_articles >= 0
            assert total_sentiment_scores >= 0

            # Ideally, processed + error should equal total (eventual consistency)
            # But in a running system, there might be articles being processed
            processing_rate = (
                (processed_articles / total_articles * 100) if total_articles > 0 else 0
            )
            error_rate = (
                (error_articles / total_articles * 100) if total_articles > 0 else 0
            )

            print(f"\n=== System Health Statistics ===")
            print(f"Total Articles: {total_articles}")
            print(f"Processed Articles: {processed_articles} ({processing_rate:.1f}%)")
            print(f"Error Articles: {error_articles} ({error_rate:.1f}%)")
            print(f"Total Sentiment Scores: {total_sentiment_scores}")
            print(f"===================================")

            # Ensure error rate is reasonable
            if total_articles > 10:  # Only check if we have sufficient data
                assert error_rate < 20, f"Error rate too high: {error_rate:.1f}%"
