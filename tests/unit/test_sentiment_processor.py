import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directories to path to allow for imports
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services")),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "services", "common")
    ),
)

from services.sentiment_processor.app.worker import FinBERTBatchAnalyzer


@pytest.fixture()
def mock_finbert_model():
    """
    Mocks the transformer model and tokenizer to prevent actual model loading
    during tests, which is slow and requires a GPU/large download.
    """
    # Create a mock tokenizer that returns a dummy structure
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {
        "input_ids": MagicMock(),
        "attention_mask": MagicMock(),
    }

    # Create a mock model that returns dummy logits
    mock_model_output = MagicMock()
    # The output needs to be a tensor-like object with a `logits` attribute
    # The logits should simulate scores for [positive, negative, neutral]
    # We use a lambda to simulate a function call that can be reused.
    mock_logits = MagicMock()
    mock_model_output.logits = mock_logits

    def softmax_side_effect(*args, **kwargs):
        # This function will be called when softmax is called.
        # It allows us to inspect the input or return different values based on input.
        # For now, just return a fixed tensor-like mock.
        predictions = MagicMock()
        # The return value of predictions.max(1) should be a tuple of (confidences, labels)
        confidences = MagicMock()
        confidences.tolist.return_value = [0.9, 0.6]
        labels = MagicMock()
        labels.tolist.return_value = [0, 1]  # positive, negative
        predictions.max.return_value = (confidences, labels)
        return predictions

    mock_logits.softmax.side_effect = softmax_side_effect

    mock_model = MagicMock()
    mock_model.return_value = mock_model_output

    # Patch the AutoTokenizer and AutoModelForSequenceClassification classes
    with patch(
        "services.sentiment_processor.app.worker.AutoTokenizer.from_pretrained",
        return_value=mock_tokenizer,
    ) as mock_auto_tokenizer, patch(
        "services.sentiment_processor.app.worker.AutoModelForSequenceClassification.from_pretrained",
        return_value=mock_model,
    ) as mock_auto_model, patch(
        "services.sentiment_processor.app.worker.torch.cuda.is_available",
        return_value=False,  # Ensure tests run on CPU mock
    ) as mock_cuda, patch(
        "services.sentiment_processor.app.worker.torch.no_grad",
    ) as mock_no_grad, patch(
        "services.sentiment_processor.app.worker.torch.device"
    ) as mock_device:
        yield {
            "tokenizer": mock_auto_tokenizer,
            "model": mock_auto_model,
            "cuda": mock_cuda,
            "no_grad": mock_no_grad,
            "device": mock_device,
        }


def test_finbert_analyzer_initialization(mock_finbert_model):
    """
    Tests if the FinBERTBatchAnalyzer initializes correctly with mocked model.
    """
    analyzer = FinBERTBatchAnalyzer()
    assert analyzer is not None
    assert analyzer.model is not None
    assert analyzer.tokenizer is not None
    assert analyzer.device is not None


def test_finbert_batch_prediction(mock_finbert_model):
    """
    Tests the batch prediction logic with a mocked model and tokenizer.
    """
    analyzer = FinBERTBatchAnalyzer()

    test_texts = ["Record profits for Q4!", "Guidance for next year is weak."]

    # Expected results based on the mocked softmax side effect
    # 1. Positive, score is confidence: 0.9
    # 2. Negative, score is -confidence: -0.6
    expected_results = [
        (0.9, "positive"),
        (-0.6, "negative"),
    ]

    results = analyzer.predict_batch(test_texts)

    assert len(results) == len(expected_results)

    # Check each result with a tolerance for floating point comparisons
    for i, (res_score, res_label) in enumerate(results):
        exp_score, exp_label = expected_results[i]
        assert res_label == exp_label
        assert pytest.approx(res_score, abs=1e-2) == exp_score
