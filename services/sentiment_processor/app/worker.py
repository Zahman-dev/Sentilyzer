import os
import sys
import time

# Redis and Celery imports
from celery import Celery, Task
from celery.signals import worker_ready
from sqlalchemy import and_

# Add project root to path for imports for consistency
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from services.common.app.db.models import RawArticle, SentimentScore
from services.common.app.db.session import create_db_session
from services.common.app.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(service_name="sentiment_worker")
logger = get_logger("sentiment_worker")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SENTIMENT_BATCH_QUEUE = "sentiment_batch_queue"

# Initialize Celery
celery_app = Celery("sentiment_worker", broker=REDIS_URL, backend=REDIS_URL)

# Global model instance (loaded once at startup)
sentiment_analyzer = None

# Constants for sentiment analysis
BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 60

# Initialize ML model
try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    MODEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML dependencies not available: {e}. Running in fallback mode.")
    MODEL_AVAILABLE = False


class FinBERTBatchAnalyzer:
    """Production-ready FinBERT sentiment analyzer optimized for batch processing.

    Model is loaded once and kept in memory for efficient batch processing.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self.model_version = "finbert-v1.0"
        self.tokenizer = None
        self.model = None
        self.device = None
        self.max_length = 512
        self.batch_size = 16  # Optimized for batch processing

        # Label mapping
        self.label_map = {0: "positive", 1: "negative", 2: "neutral"}

        self._load_model()

    def _load_model(self):
        """Load FinBERT model and tokenizer. Called once at startup."""
        if not MODEL_AVAILABLE:
            logger.warning(
                "ML dependencies not available. Using fallback sentiment analysis."
            )
            return

        try:
            logger.info(f"Loading FinBERT model: {self.model_name}")
            start_time = time.time()

            # Set device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode

            # Test inference to warm up the model
            test_text = "The market is showing positive trends."
            _ = self._predict_single(test_text)

            load_time = time.time() - start_time
            logger.info(f"FinBERT model loaded successfully in {load_time:.2f} seconds")

        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e!s}")
            logger.warning("Falling back to keyword-based sentiment analysis")
            self.model = None
            self.tokenizer = None

    def _predict_single(self, text: str) -> tuple[float, str]:
        """Single text prediction using FinBERT."""
        if not self.model or not self.tokenizer:
            return self._fallback_sentiment(text)

        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=self.max_length,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                confidence, predicted = torch.max(logits, 1)

                confidence_score = confidence.item()
                predicted_label = self.label_map[int(predicted.item())]

                # Convert to sentiment score (-1 to 1 range)
                if predicted_label == "positive":
                    sentiment_score = confidence_score
                elif predicted_label == "negative":
                    sentiment_score = -confidence_score
                else:  # neutral
                    sentiment_score = 0.0

                return sentiment_score, predicted_label

        except Exception as e:
            logger.error(f"Error in FinBERT prediction: {e!s}")
            return self._fallback_sentiment(text)

    def predict_batch(self, texts: list[str]) -> list[tuple[float, str]]:
        """Batch prediction for maximum throughput efficiency."""
        if not self.model or not self.tokenizer:
            return [self._fallback_sentiment(text) for text in texts]

        if not texts:
            return []

        try:
            logger.info(f"Processing batch of {len(texts)} texts")

            # Process in chunks if batch is too large
            results = []
            for i in range(0, len(texts), self.batch_size):
                chunk = texts[i : i + self.batch_size]
                chunk_results = self._process_chunk(chunk)
                results.extend(chunk_results)

            logger.info(f"Successfully processed batch of {len(texts)} texts")
            return results

        except Exception as e:
            logger.error(f"Error in batch prediction: {e!s}")
            return [self._fallback_sentiment(text) for text in texts]

    def _process_chunk(self, texts: list[str]) -> list[tuple[float, str]]:
        """Process a chunk of texts through the model."""
        if not self.model or not self.tokenizer:
            return [self._fallback_sentiment(text) for text in texts]

        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.max_length,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Predict batch
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            confidences, predicted_labels = torch.max(logits, 1)

            results = []
            for conf, pred in zip(confidences, predicted_labels, strict=False):
                confidence_score = conf.item()
                predicted_label = self.label_map[int(pred.item())]

                # Convert to sentiment score
                if predicted_label == "positive":
                    sentiment_score = confidence_score
                elif predicted_label == "negative":
                    sentiment_score = -confidence_score
                else:  # neutral
                    sentiment_score = 0.0

                results.append((sentiment_score, predicted_label))

            return results

    def _fallback_sentiment(self, text: str) -> tuple[float, str]:
        """Fallback keyword-based sentiment analysis when FinBERT is not available."""
        positive_keywords = [
            "growth",
            "profit",
            "gain",
            "increase",
            "rise",
            "up",
            "positive",
            "strong",
            "bull",
            "bullish",
            "buy",
            "upgrade",
            "outperform",
            "revenue",
            "earnings",
            "beat",
            "exceed",
            "high",
            "good",
        ]

        negative_keywords = [
            "loss",
            "fall",
            "decline",
            "drop",
            "down",
            "negative",
            "weak",
            "bear",
            "bearish",
            "sell",
            "downgrade",
            "underperform",
            "deficit",
            "miss",
            "low",
            "bad",
            "poor",
            "crisis",
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)

        if positive_count > negative_count:
            return 0.6, "positive"
        elif negative_count > positive_count:
            return -0.6, "negative"
        else:
            return 0.0, "neutral"


@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    """Initialize the sentiment analyzer when worker starts.

    This ensures the model is loaded once and kept in memory.
    """
    global sentiment_analyzer
    logger.info("Initializing sentiment analyzer...")
    sentiment_analyzer = FinBERTBatchAnalyzer()
    logger.info("Worker ready and sentiment analyzer initialized.")


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_jitter=True,
    name="services.sentiment_processor.app.worker.process_sentiment_batch",
)
def process_sentiment_batch(self: Task, article_ids: list[int]):
    """Celery task to process a batch of articles for sentiment analysis.

    Args:
        self (Task): The Celery Task instance.
        article_ids (list[int]): A list of article IDs to process.
    """
    global sentiment_analyzer

    if not article_ids:
        logger.warning("Received empty article_ids list")
        return {"status": "success", "processed": 0, "message": "Empty batch"}

    logger.info(
        f"Starting batch processing for {len(article_ids)} articles: {article_ids}"
    )

    try:
        # Step 1: Batch fetch articles from database
        session = create_db_session()
        try:
            # Single database query to fetch all articles
            articles = (
                session.query(RawArticle)
                .filter(
                    and_(
                        RawArticle.id.in_(article_ids),
                        RawArticle.is_processed.is_(False),
                        RawArticle.has_error.is_(False),
                    )
                )
                .all()
            )

            if not articles:
                logger.warning(f"No valid articles found for IDs: {article_ids}")
                return {
                    "status": "success",
                    "processed": 0,
                    "message": "No valid articles found",
                }

            logger.info(f"Fetched {len(articles)} articles from database")

            # Step 2: Prepare texts for batch analysis
            article_texts = []
            article_map = {}  # Map index to article for result matching

            for idx, article in enumerate(articles):
                # Combine headline and article_text for better sentiment analysis
                combined_text = f"{article.headline} {article.article_text}"
                article_texts.append(combined_text)
                article_map[idx] = article

            # Step 3: Batch sentiment analysis
            if not sentiment_analyzer:
                raise Exception("Sentiment analyzer not initialized")

            logger.info(
                f"Starting batch sentiment analysis for {len(article_texts)} texts"
            )
            sentiment_results = sentiment_analyzer.predict_batch(article_texts)

            # Step 4: Prepare bulk insert data
            sentiment_records = []
            processed_article_ids = []

            for idx, (sentiment_score, sentiment_label) in enumerate(sentiment_results):
                article = article_map[idx]

                # Create sentiment score record
                sentiment_record = SentimentScore(
                    article_id=article.id,
                    model_version=sentiment_analyzer.model_version,
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label,
                )
                sentiment_records.append(sentiment_record)
                processed_article_ids.append(article.id)

            # Step 5: Bulk save to database
            if sentiment_records:
                # Add all sentiment scores in one transaction
                session.add_all(sentiment_records)

                # Update processed articles
                session.query(RawArticle).filter(
                    RawArticle.id.in_(processed_article_ids)
                ).update({"is_processed": True}, synchronize_session=False)

                session.commit()

                logger.info(
                    f"Successfully processed and saved {len(sentiment_records)} sentiment analyses"
                )

                return {
                    "status": "success",
                    "processed": len(sentiment_records),
                    "article_ids": processed_article_ids,
                }
            else:
                logger.warning("No sentiment records to save")
                return {
                    "status": "success",
                    "processed": 0,
                    "message": "No records to save",
                }

        finally:
            session.close()

    except Exception as e:
        # Robust error handling - Poison Pill Prevention
        logger.error(f"Error processing batch {article_ids}: {e!s}", exc_info=True)

        try:
            # Mark all articles in this batch as having errors
            session = create_db_session()
            try:
                updated_count = (
                    session.query(RawArticle)
                    .filter(RawArticle.id.in_(article_ids))
                    .update({"has_error": True}, synchronize_session=False)
                )
                session.commit()

                logger.info(
                    f"Marked {updated_count} articles as having errors to prevent reprocessing"
                )

            finally:
                session.close()

        except Exception as db_error:
            logger.error(
                f"Failed to update error status for articles {article_ids}: {db_error!s}"
            )

        # Don't raise the exception - this prevents the task from being retried
        # and becoming a "poison pill" that blocks the queue
        return {
            "status": "error",
            "processed": 0,
            "error": str(e),
            "article_ids": article_ids,
        }


if __name__ == "__main__":
    # Start the Celery worker
    logger.info("Starting Celery worker for sentiment batch processing")
    celery_app.start()
