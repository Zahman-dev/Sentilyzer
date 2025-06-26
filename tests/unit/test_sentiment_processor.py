import unittest
import sys
import os

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'sentiment_processor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'common'))


class TestSentimentProcessor(unittest.TestCase):
    """Unit tests for SentimentProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid import issues during discovery
        from services.sentiment_processor.app.main import SentimentProcessor
        self.processor = SentimentProcessor.__new__(SentimentProcessor)
        self.processor.model_version = "test-v1.0"
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis with positive text."""
        text = "The company reported strong growth and increased profits this quarter."
        score, label = self.processor.analyze_sentiment(text)
        
        self.assertEqual(label, "positive")
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)
        self.assertGreaterEqual(score, -1.0)
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis with negative text."""
        text = "The company reported significant losses and declining sales this quarter."
        score, label = self.processor.analyze_sentiment(text)
        
        self.assertEqual(label, "negative")
        self.assertLess(score, 0)
        self.assertLessEqual(score, 1.0)
        self.assertGreaterEqual(score, -1.0)
    
    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis with neutral text."""
        text = "The company held its annual meeting and discussed standard procedures."
        score, label = self.processor.analyze_sentiment(text)
        
        self.assertEqual(label, "neutral")
        self.assertLessEqual(score, 1.0)
        self.assertGreaterEqual(score, -1.0)
    
    def test_analyze_sentiment_empty_text(self):
        """Test sentiment analysis with empty text."""
        text = ""
        score, label = self.processor.analyze_sentiment(text)
        
        self.assertIn(label, ["positive", "negative", "neutral"])
        self.assertLessEqual(score, 1.0)
        self.assertGreaterEqual(score, -1.0)


if __name__ == '__main__':
    unittest.main() 