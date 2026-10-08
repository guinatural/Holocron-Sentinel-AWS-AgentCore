"""Unit tests for SecurityGroup Scanner."""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.security_group_scanner import SecurityGroupScanner


class TestSecurityGroupScanner:
    """Test SecurityGroup scanner functionality."""
    
    def test_init(self):
        """Test scanner initialization."""
        scanner = SecurityGroupScanner(tenant_id="test_tenant", region="us-east-1")
        
        assert scanner.tenant_id == "test_tenant"
        assert scanner.region == "us-east-1"
        assert scanner.findings == []
    
    @patch('app.agents.security_group_scanner.boto3.client')
    def test_ec2_client_creation(self, mock_client):
        """Test EC2 client creation."""
        mock_ec2 = Mock()
        mock_client.return_value = mock_ec2
        
        scanner = SecurityGroupScanner(tenant_id="test_tenant", region="us-east-1")
        _ = scanner.ec2_client
        
        mock_client.assert_called_once_with('ec2', region_name="us-east-1")
    
    @patch('app.agents.security_group_scanner.boto3.client')
    def test_scan_all_security_groups(self, mock_client):
        """Test scanning security groups."""
        mock_ec2 = Mock()
        mock_client.return_value = mock_ec2
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': []
        }
        
        scanner = SecurityGroupScanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner.scan_all_security_groups()
        
        assert isinstance(findings, list)
    
    @patch('app.agents.security_group_scanner.boto3.client')
    def test_scan_security_group(self, mock_client):
        """Test scanning a specific security group."""
        mock_ec2 = Mock()
        mock_client.return_value = mock_ec2
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{
                'GroupId': 'sg-123456',
                'GroupName': 'default',
                'IpPermissions': []
            }]
        }
        
        scanner = SecurityGroupScanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner.scan_security_group('sg-123456')
        
        assert isinstance(findings, list)
    
    def test_dangerous_ports_detection(self):
        """Test dangerous ports are defined."""
        scanner = SecurityGroupScanner(tenant_id="test_tenant", region="us-east-1")
        
        dangerous_ports = scanner.DANGEROUS_PORTS
        
        assert 22 in dangerous_ports  # SSH
        assert 3389 in dangerous_ports  # RDP
        assert 3306 in dangerous_ports  # MySQL
        assert 5432 in dangerous_ports  # PostgreSQL
        assert 9200 in dangerous_ports  # Elasticsearch
        assert 27017 in dangerous_ports  # MongoDB
        assert 6379 in dangerous_ports  # Redis
    
    def test_dangerous_port_severities(self):
        """Test dangerous ports have correct severities."""
        scanner = SecurityGroupScanner(tenant_id="test_tenant", region="us-east-1")
        
        ports = scanner.DANGEROUS_PORTS
        
        # SSH and RDP should be critical
        assert ports[22]['severity'] == 'critical'
        assert ports[3389]['severity'] == 'critical'
        
        # Database ports should be high
        assert ports[3306]['severity'] == 'high'
        assert ports[5432]['severity'] == 'high'
        assert ports[9200]['severity'] == 'high'
        assert ports[27017]['severity'] == 'high'
        assert ports[6379]['severity'] == 'high'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
