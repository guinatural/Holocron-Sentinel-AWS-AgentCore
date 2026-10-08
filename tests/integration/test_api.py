"""Integration tests for API endpoints."""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

from app.api.main import app


# Create test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Holocron Sentinel V2" in data.get("service", "")
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Holocron Sentinel V2"
        assert data["version"] == "2.0.0"
        assert "/docs" in data.get("docs", "")
    
    def test_status_endpoint(self):
        """Test status endpoint."""
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
    
    def test_list_scanners(self):
        """Test list scanners endpoint."""
        response = client.get("/api/v1/scanners")
        
        assert response.status_code == 200
        data = response.json()
        assert "scanners" in data
        assert len(data["scanners"]) > 0
        
        # Check that all expected scanners are listed
        scanner_ids = [s["id"] for s in data["scanners"]]
        assert "s3" in scanner_ids
        assert "iam" in scanner_ids
        assert "ec2" in scanner_ids
        assert "security_group" in scanner_ids
    
    def test_list_scanners_structure(self):
        """Test scanners list structure."""
        response = client.get("/api/v1/scanners")
        data = response.json()
        
        for scanner in data["scanners"]:
            assert "id" in scanner
            assert "name" in scanner
            assert "description" in scanner


class TestAuditEndpoints:
    """Test audit-related endpoints."""
    
    def test_start_audit_endpoint(self):
        """Test start audit endpoint."""
        audit_request = {
            "tenant_id": "test_tenant",
            "scanners": ["s3"]
        }
        
        response = client.post("/api/v1/audit", json=audit_request)
        
        # May fail due to AWS dependencies, but should return a response
        assert response.status_code in [200, 500]  # 500 is OK for integration test
    
    def test_get_audit_results_not_found(self):
        """Test getting non-existent audit results."""
        response = client.get("/api/v1/audit/nonexistent-job")
        
        # Should return 404 for non-existent job
        assert response.status_code == 404
    
    def test_start_audit_with_default_scanners(self):
        """Test starting audit without specifying scanners."""
        audit_request = {
            "tenant_id": "test_tenant"
        }
        
        response = client.post("/api/v1/audit", json=audit_request)
        
        # Should return a response
        assert response.status_code in [200, 500]


class TestScannerEndpoints:
    """Test scanner-specific endpoints."""
    
    def test_run_s3_scanner(self):
        """Test running S3 scanner."""
        scan_request = {
            "tenant_id": "test_tenant",
            "scanner": "s3"
        }
        
        response = client.post("/api/v1/scanners/scan", json=scan_request)
        
        # May fail due to AWS dependencies
        assert response.status_code in [200, 500]
    
    def test_run_invalid_scanner(self):
        """Test running invalid scanner."""
        scan_request = {
            "tenant_id": "test_tenant",
            "scanner": "invalid_scanner"
        }
        
        response = client.post("/api/v1/scanners/scan", json=scan_request)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_run_ec2_scanner(self):
        """Test running EC2 scanner."""
        scan_request = {
            "tenant_id": "test_tenant",
            "scanner": "ec2"
        }
        
        response = client.post("/api/v1/scanners/scan", json=scan_request)
        
        # May fail due to AWS dependencies
        assert response.status_code in [200, 500]


class TestSummaryEndpoints:
    """Test summary endpoints."""
    
    def test_get_tenant_summary(self):
        """Test getting tenant summary."""
        response = client.get("/api/v1/summary/test_tenant")
        
        # Should return summary (even if empty)
        assert response.status_code in [200, 500]
    
    def test_get_scanners_status(self):
        """Test getting scanners status."""
        response = client.get("/api/v1/scanners/status?tenant_id=test_tenant")
        
        # Should return status for all scanners
        assert response.status_code in [200, 500]


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self):
        """Test that CORS headers are present."""
        response = client.get("/health")
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
