import os
import sys
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

# Add project root to path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Add common library to path
common_path = os.path.join(project_root, "services", "common")
sys.path.insert(0, common_path)


class TestDataIngestor(unittest.TestCase):
    """Unit tests for DataIngestor class."""

    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid import issues during discovery
        from services.data_ingestor.app.main import DataIngestor

        # Mock the database session
        with patch("services.data_ingestor.app.main.create_db_session") as mock_session:
            self.mock_session = Mock()
            mock_session.return_value = self.mock_session
            self.ingestor = DataIngestor()

    def test_extract_article_content_with_summary(self):
        """Test content extraction with summary field."""
        # Mock RSS entry with summary
        mock_entry = Mock()
        mock_entry.summary = "<p>This is a test article summary.</p>"
        mock_entry.title = "Test Article"

        content = self.ingestor.extract_article_content(mock_entry)
        self.assertEqual(content, "This is a test article summary.")

    def test_extract_article_content_with_description(self):
        """Test content extraction with description field."""
        # Mock RSS entry with description
        mock_entry = Mock()
        mock_entry.summary = None
        mock_entry.description = "<div>This is a test description.</div>"
        mock_entry.title = "Test Article"

        content = self.ingestor.extract_article_content(mock_entry)
        self.assertEqual(content, "This is a test description.")

    def test_extract_article_content_fallback_to_title(self):
        """Test content extraction fallback to title."""
        # Mock RSS entry with no content fields
        mock_entry = Mock()
        mock_entry.summary = None
        mock_entry.description = None
        mock_entry.content = []
        mock_entry.title = "Test Article Title"

        content = self.ingestor.extract_article_content(mock_entry)
        self.assertEqual(content, "Test Article Title")

    def test_parse_published_date_with_published_parsed(self):
        """Test date parsing with published_parsed field."""
        # Mock RSS entry with published_parsed
        mock_entry = Mock()
        mock_entry.published_parsed = (2023, 12, 25, 10, 30, 0, 0, 0, 0)
        mock_entry.updated_parsed = None

        date = self.ingestor.parse_published_date(mock_entry)
        expected_date = datetime(2023, 12, 25, 10, 30, 0)
        self.assertEqual(date, expected_date)

    def test_parse_published_date_fallback_to_current(self):
        """Test date parsing fallback to current time."""
        # Mock RSS entry with no date fields
        mock_entry = Mock()
        mock_entry.published_parsed = None
        mock_entry.updated_parsed = None

        date = self.ingestor.parse_published_date(mock_entry)
        self.assertIsInstance(date, datetime)
        # Should be close to current time (within 1 second)
        now = datetime.utcnow()
        time_diff = abs((date - now).total_seconds())
        self.assertLess(time_diff, 1)


if __name__ == "__main__":
    unittest.main()
