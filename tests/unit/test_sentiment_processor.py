"""Unit tests for the Sentiment Processor worker."""

from services.sentiment_processor.app.worker import FinBERTBatchAnalyzer

# --- Test Suite for FinBERTBatchAnalyzer ---


class TestFinBERTBatchAnalyzer:
    """
    Tests the core logic of the sentiment analyzer,
    focusing on fallback mechanisms and batching, without loading the real model.
    """

    def test_initialization_with_real_model(self):
        """
        Gercek FinBERT modelinin basariyla yuklenip yuklenmedigini test eder.
        """
        analyzer = FinBERTBatchAnalyzer()
        assert analyzer.model is not None
        assert analyzer.tokenizer is not None
        assert analyzer.model_version == "finbert-v1.0"

    def test_batch_prediction_with_real_model(self):
        """
        Gercek model ile batch prediction ciktisinin dogru formatta ve anlamli oldugunu test eder.
        """
        analyzer = FinBERTBatchAnalyzer()
        texts = [
            "The market is showing positive growth and gains.",
            "The company reported a significant loss and poor performance.",
            "The results were neutral and inconclusive."
        ]
        results = analyzer.predict_batch(texts)
        assert len(results) == 3
        for score, label in results:
            assert isinstance(score, float)
            assert label in ["positive", "negative", "neutral"]

    def test_single_prediction_with_real_model(self):
        """
        Gercek model ile tekli prediction ciktisinin dogru formatta ve anlamli oldugunu test eder.
        """
        analyzer = FinBERTBatchAnalyzer()
        score, label = analyzer._predict_single("The company is performing exceptionally well.")
        assert isinstance(score, float)
        assert label in ["positive", "negative", "neutral"]
