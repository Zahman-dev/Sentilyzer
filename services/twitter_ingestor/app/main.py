import os
from datetime import datetime

from services.common.app.db.models import RawArticle
from services.common.app.db.session import create_db_session
from services.common.app.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(service_name="twitter_ingestor")
logger = get_logger("twitter_ingestor")


def main():
    logger.info("Starting Twitter Ingestor...")
    db_session = create_db_session()
    if not db_session:
        logger.error("Failed to create database session.")
        return

    try:
        # This is a placeholder for the Twitter integration logic.
        logger.info("Fetching tweets (placeholder)...")
        dummy_article = RawArticle(
            source="twitter_placeholder",
            headline="Placeholder Tweet",
            article_text="This is the content of a placeholder tweet.",
            article_url=f"https://twitter.com/placeholder/{datetime.utcnow().timestamp()}",
            published_at=datetime.utcnow(),
            is_processed=False,
            has_error=False,
        )
        db_session.add(dummy_article)
        db_session.commit()
        logger.info("Successfully ingested a placeholder tweet.")

    except Exception as e:
        logger.error(f"An error occurred during ingestion: {e}", exc_info=True)
    finally:
        if db_session:
            db_session.close()


if __name__ == "__main__":
    main()
