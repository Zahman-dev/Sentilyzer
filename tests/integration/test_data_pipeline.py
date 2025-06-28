"""
End-to-end tests for the main data processing pipeline.
"""

from datetime import datetime, timezone

import pytest

from services.common.app.db.models import RawArticle, SentimentScore
from services.sentiment_processor.app.worker import (
    FinBERTBatchAnalyzer,
    process_sentiment_batch,
)

# --- Test Suite for the Data Pipeline ---


class TestDataPipeline:
    """
    Tests the core data flow:
    1. A raw article exists in the database.
    2. The sentiment processing task is called.
    3. A sentiment score is correctly created and linked to the article.
    """

    @pytest.fixture(autouse=True, scope="class")
    def _setup_environment(self, db_engine, db_session_factory):
        """
        Test ortaminda worker'in engine, session factory ve sentiment_analyzer'ini override eder.
        """
        import services.common.app.db.session as db_session_mod
        import services.sentiment_processor.app.worker as worker_mod

        # Orijinalleri sakla
        orig_get_engine = db_session_mod.get_engine
        orig_get_session_factory = db_session_mod.get_session_factory
        orig_create_db_session = db_session_mod.create_db_session
        orig_sentiment_analyzer = worker_mod.sentiment_analyzer

        # Testteki engine ve session factory'yi döndüren fonksiyonlar
        def test_get_engine(*args, **kwargs):
            return db_engine
        def test_get_session_factory(engine):
            return db_session_factory
        def test_create_db_session(SessionLocal=None):
            if SessionLocal is None:
                SessionLocal = db_session_factory
            return SessionLocal()

        # Override
        db_session_mod.get_engine = test_get_engine
        db_session_mod.get_session_factory = test_get_session_factory
        db_session_mod.create_db_session = test_create_db_session
        worker_mod.sentiment_analyzer = FinBERTBatchAnalyzer()

        yield

        # Restore
        db_session_mod.get_engine = orig_get_engine
        db_session_mod.get_session_factory = orig_get_session_factory
        db_session_mod.create_db_session = orig_create_db_session
        worker_mod.sentiment_analyzer = orig_sentiment_analyzer

    def test_full_pipeline(self, db_session):
        """
        Test the complete data pipeline from raw article to sentiment score.
        """
        # --- 1. Arrange (Setup) ---
        # Create a test raw article
        raw_article = RawArticle(
            headline="Test Article Title",
            article_text="This is a positive test article about market growth and success.",
            source="test_source",
            article_url="https://test.com/article",
            published_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            is_processed=False,
        )
        db_session.add(raw_article)
        db_session.commit()
        db_session.refresh(raw_article)

        # --- 2. Act (Execute) ---
        # Process the article through the sentiment pipeline
        result = process_sentiment_batch.s(article_ids=[raw_article.id]).apply()

        # --- 3. Assert (Verification) ---
        # Check the result first
        assert result.get()["status"] == "success"
        assert result.get()["processed"] == 1

        # Session'i expire et, böylece güncel veriyi çeker
        db_session.expire_all()

        # Query the database for the updated article and sentiment score
        updated_article = (
            db_session.query(RawArticle)
            .filter_by(id=raw_article.id)
            .first()
        )
        assert updated_article is not None
        assert updated_article.is_processed is True

        # Check that a sentiment score was created and linked
        sentiment_score = (
            db_session.query(SentimentScore)
            .filter_by(article_id=raw_article.id)
            .first()
        )
        assert sentiment_score is not None
        assert sentiment_score.sentiment_score is not None
        assert sentiment_score.sentiment_label is not None
        assert sentiment_score.model_version is not None
        assert sentiment_score.processed_at is not None
