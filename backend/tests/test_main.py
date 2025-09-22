"""Tests for main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app


class TestMainApplication:
    """Test main FastAPI application."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["version"] == "1.0.0"
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert isinstance(data["timestamp"], (int, float))
    
    def test_404_handler(self):
        """Test custom 404 handler."""
        response = self.client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Resource not found"
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.options("/")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    @patch('app.main.create_tables')
    def test_startup_event(self, mock_create_tables):
        """Test application startup event."""
        # This is tested implicitly when the TestClient is created
        # The lifespan context manager runs during client initialization
        mock_create_tables.assert_called_once()
    
    def test_api_documentation(self):
        """Test API documentation endpoints."""
        # Test OpenAPI docs
        response = self.client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = self.client.get("/redoc")
        assert response.status_code == 200
        
        # Test OpenAPI schema
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "info" in schema
        assert schema["info"]["title"] == "Personal Event Photo Gallery API"
        assert schema["info"]["version"] == "1.0.0"
    
    def test_middleware_headers(self):
        """Test that middleware adds expected headers."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        # Check for process time header added by LoggingMiddleware
        assert "x-process-time" in response.headers
        
        # Verify it's a valid float
        process_time = float(response.headers["x-process-time"])
        assert process_time >= 0
    
    def test_static_files_mount(self):
        """Test static files are mounted correctly."""
        # This would require actual static files to test properly
        # For now, just verify the mount doesn't cause errors
        response = self.client.get("/static/nonexistent.jpg")
        # Should return 404 for non-existent file, not 500
        assert response.status_code == 404


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


def test_application_metadata(test_client):
    """Test application metadata."""
    response = test_client.get("/openapi.json")
    schema = response.json()
    
    assert schema["info"]["title"] == "Personal Event Photo Gallery API"
    assert schema["info"]["description"] == "API for Personal Event Photo Gallery with Smart Face Recognition"
    assert schema["info"]["version"] == "1.0.0"


def test_error_handling_middleware():
    """Test error handling middleware."""
    client = TestClient(app)
    
    # Test that unhandled exceptions are caught
    with patch('app.routers.persons.router') as mock_router:
        mock_router.side_effect = Exception("Test exception")
        
        # This would test the error handling, but requires actual router setup
        # For now, we'll test that the middleware is properly configured
        assert any(
            middleware.cls.__name__ == "ErrorHandlingMiddleware" 
            for middleware in app.user_middleware
        )