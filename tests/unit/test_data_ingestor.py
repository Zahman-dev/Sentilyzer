"""Unit tests for the Data Ingestor tasks."""

import pytest

from services.data_ingestor.app.tasks import TickerExtractor

# --- Test Suite for TickerExtractor ---


class TestTickerExtractor:
    """
    Tests the logic of the TickerExtractor to ensure it accurately finds
    tickers from text and avoids common false positives.
    """

    @pytest.fixture(scope="class")
    def extractor(self):
        """Returns a single instance of the TickerExtractor for all tests in this class."""
        return TickerExtractor()

    # Parametrized test to cover multiple company name mappings
    @pytest.mark.parametrize(
        ("company_name", "expected_ticker"),
        [
            ("Apple", "AAPL"),
            ("Microsoft", "MSFT"),
            ("JPMorgan", "JPM"),
            ("NVIDIA", "NVDA"),
            ("Amazon's earnings", "AMZN"),
            ("a story about google", "GOOGL"),
        ],
    )
    def test_ticker_extraction_from_company_map(
        self, extractor, company_name, expected_ticker
    ):
        """Tests extracting tickers by matching known company names."""
        text = f"A news article about {company_name}."
        ticker = extractor.extract_ticker_from_text(text)
        assert ticker == expected_ticker

    # Parametrized test to cover multiple regex patterns
    @pytest.mark.parametrize(
        ("text", "expected_ticker"),
        [
            ("The price of $TSLA is rising.", "TSLA"),
            ("A look at the META stock.", "META"),
            ("Investing in Netflix (NFLX) shares.", "NFLX"),
            ("A report from NYSE: BA.", "BA"),
            ("Breaking news on NASDAQ: COIN.", "COIN"),
            ("Is $XYZ a good buy?", "XYZ"),
        ],
    )
    def test_ticker_extraction_from_regex(self, extractor, text, expected_ticker):
        """Tests extracting tickers using various regex patterns."""
        ticker = extractor.extract_ticker_from_text(text)
        assert ticker == expected_ticker

    # Parametrized test to check for common words that can be mistaken for tickers
    @pytest.mark.parametrize(
        "text",
        [
            "THE market is open.",
            "FOR a limited time only.",
            "A new bill was passed.",
            "This is a test of the system.",
            "We will now begin.",
        ],
    )
    def test_ticker_extraction_avoids_false_positives(self, extractor, text):
        """
        Tests that the extractor does not incorrectly identify common English
        words as ticker symbols.
        """
        ticker = extractor.extract_ticker_from_text(text)
        assert ticker is None

    def test_extraction_priority(self, extractor):
        """
        Tests that the company name map takes priority over regex patterns.
        For example, 'Meta' should be found before a potential regex match on another word.
        """
        text = "A story about Meta (formerly Facebook) and its stock."
        ticker = extractor.extract_ticker_from_text(text)
        assert ticker == "META"

    def test_no_ticker_found(self, extractor):
        """Tests that None is returned when no ticker can be found in the text."""
        text = "A story about the economy with no company names or symbols."
        ticker = extractor.extract_ticker_from_text(text)
        assert ticker is None
