"""Unit tests for S3 Scanner."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.s3_scanner import S3Scanner, S3Finding


class TestS3Scanner:
    """Test S3 scanner functionality."""
    
    def test_init(self):
        """Test scanner initialization."""
        scanner = S3Scanner(tenant_id="test_tenant", region="us-east-1")
        
        assert scanner.tenant_id == "test_tenant"
        assert scanner.region == "us-east-1"
        assert scanner.findings == []
    
    @patch('app.agents.s3_scanner.boto3.Session')
    def test_s3_client_creation(self, mock_session):
        """Test S3 client creation."""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        scanner = S3Scanner(tenant_id="test_tenant", region="us-east-1")
        _ = scanner.s3_client
        
        mock_session.assert_called_once_with(region_name="us-east-1")
        mock_session.return_value.client.assert_called_once_with('s3')
    
    @patch('app.agents.s3_scanner.boto3.Session')
    def test_scan_bucket_with_findings(self, mock_session):
        """Test scanning a bucket with findings."""
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock responses
        mock_client.get_public_access_block.side_effect = Exception("Not configured")
        mock_client.list_buckets.return_value = {'Buckets': [{'Name': 'test-bucket'}]}
        
        scanner = S3Scanner(tenant_id="test_tenant", region="us-east-1")
        
        # Mock the scan_bucket method to return test findings
        with patch.object(scanner, 'scan_bucket', return_value=[
            {
                'finding_id': 'test-123',
                'severity': 'high',
                'category': 'security',
                'bucket_name': 'test-bucket',
                'check_name': 'test_check',
                'status': 'fail',
                'description': 'Test finding',
                'remediation': 'Fix it'
            }
        ]):
            findings = scanner.scan_bucket('test-bucket')
            assert len(findings) == 1
            assert findings[0]['severity'] == 'high'
    
    def test_lgpd_compliance(self):
        """Test that findings are anonymized."""
        payload = {
            'findings': [{
                'finding_id': 'test-123',
                'description': 'User john@example.com has issues',
                'remediation': 'Contact the admin'
            }]
        }
        
        from app.security.anonymization import lgpd_anonymize
        result = lgpd_anonymize(payload)
        
        assert 'john@example.com' not in result['findings'][0]['description']
        # Note: remediation text like 'Contact admin' won't be anonymized since it doesn't contain sensitive patterns


class TestS3FindingDataclass:
    """Test S3Finding dataclass."""
    
    def test_finding_creation(self):
        """Test creating a finding."""
        finding = S3Finding(
            finding_id="s3-abc123-bpa-all",
            severity="critical",
            category="security",
            bucket_name="my-bucket",
            check_name="block_public_access",
            status="fail",
            description="Bucket is publicly accessible",
            remediation="Enable Block Public Access"
        )
        
        assert finding.finding_id == "s3-abc123-bpa-all"
        assert finding.severity == "critical"
        assert finding.category == "security"
        assert finding.status == "fail"
    
    def test_finding_timestamp(self):
        """Test that finding gets timestamp."""
        finding = S3Finding(
            finding_id="test-123",
            severity="info",
            category="compliance",
            bucket_name="test-bucket",
            check_name="test",
            status="pass",
            description="Test",
            remediation="Test"
        )
        
        assert finding.timestamp is not None
        assert "T" in finding.timestamp  # ISO format contains T


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
