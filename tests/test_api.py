"""
Tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        # Create a fake file with wrong extension
        files = {"file": ("test.txt", b"dummy content", "text/plain")}
        response = client.post("/api/v1/upload", files=files)
        
        # Should return 400 error
        assert response.status_code == 400
    
    def test_status_nonexistent_task(self):
        """Test status check for nonexistent task"""
        response = client.get("/api/v1/status/nonexistent_task_id")
        assert response.status_code == 404
    
    def test_result_nonexistent_task(self):
        """Test result retrieval for nonexistent task"""
        response = client.get("/api/v1/result/nonexistent_task_id")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

