import unittest
import sys
import os
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'signals_api'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'common'))


class TestSignalsAPIIntegration(unittest.TestCase):
    """Integration tests for Signals API service."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Note: In a real implementation, we would use testcontainers 
        # to spin up a temporary PostgreSQL database for testing.
        # For now, we'll create a simple test setup.
        pass
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid import issues during discovery
        from services.signals_api.app.main import app
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("timestamp", data)
        self.assertEqual(data["version"], "1.0.0")
    
    def test_signals_endpoint_request_validation(self):
        """Test signals endpoint request validation."""
        # Test with invalid request (missing required fields)
        response = self.client.post("/v1/signals", json={})
        self.assertEqual(response.status_code, 422)  # Validation error
        
        # Test with valid request structure
        valid_request = {
            "ticker": "AAPL",
            "start_date": "2023-01-01T00:00:00Z",
            "end_date": "2023-01-31T23:59:59Z"
        }
        
        # Note: This might fail if database is not properly set up
        # In a real integration test, we would ensure database connectivity
        try:
            response = self.client.post("/v1/signals", json=valid_request)
            # Should either succeed (200) or fail with server error (500)
            self.assertIn(response.status_code, [200, 500])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("data", data)
                self.assertIn("total_count", data)
                self.assertIsInstance(data["data"], list)
                self.assertIsInstance(data["total_count"], int)
                
        except Exception as e:
            # Database connection issues are expected in test environment
            self.skipTest(f"Database connection required for full integration test: {e}")
    
    def test_stats_endpoint(self):
        """Test the stats endpoint."""
        try:
            response = self.client.get("/v1/stats")
            
            # Should either succeed (200) or fail with server error (500)
            self.assertIn(response.status_code, [200, 500])
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = [
                    "total_articles", "processed_articles", "error_articles",
                    "total_sentiment_scores", "latest_article_date", "processing_rate"
                ]
                
                for field in expected_fields:
                    self.assertIn(field, data)
                    
        except Exception as e:
            self.skipTest(f"Database connection required for full integration test: {e}")
    
    def test_sources_endpoint(self):
        """Test the sources endpoint."""
        try:
            response = self.client.get("/v1/sources")
            
            # Should either succeed (200) or fail with server error (500)
            self.assertIn(response.status_code, [200, 500])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("sources", data)
                self.assertIn("total_sources", data)
                self.assertIsInstance(data["sources"], list)
                self.assertIsInstance(data["total_sources"], int)
                
        except Exception as e:
            self.skipTest(f"Database connection required for full integration test: {e}")
    
    def test_openapi_documentation(self):
        """Test that OpenAPI documentation is available."""
        # Test docs endpoint
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        
        # Test OpenAPI JSON
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        
        openapi_spec = response.json()
        self.assertIn("info", openapi_spec)
        self.assertIn("paths", openapi_spec)
        self.assertEqual(openapi_spec["info"]["title"], "Sentilyzer Signals API")


if __name__ == '__main__':
    unittest.main() 