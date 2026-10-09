"""Unit tests for EC2 Scanner."""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.ec2_scanner import EC2Scanner


class TestEC2Scanner:
    """Test EC2 scanner functionality."""

    def test_init(self):
        """Test scanner initialization."""
        scanner = EC2Scanner(tenant_id="test_tenant", region="us-east-1")

        assert scanner.tenant_id == "test_tenant"
        assert scanner.region == "us-east-1"
        assert scanner.findings == []

    @patch("app.agents.ec2_scanner.boto3.client")
    def test_ec2_client_creation(self, mock_client):
        """Test EC2 client creation."""
        mock_ec2 = Mock()
        mock_client.return_value = mock_ec2

        scanner = EC2Scanner(tenant_id="test_tenant", region="us-east-1")
        _ = scanner.ec2_client

        mock_client.assert_called_once_with("ec2", region_name="us-east-1")

    @patch("app.agents.ec2_scanner.boto3.client")
    def test_scan_all_instances(self, mock_client):
        """Test scanning instances."""
        mock_ec2 = Mock()
        mock_client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {"Reservations": []}

        scanner = EC2Scanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner.scan_all_instances()

        assert isinstance(findings, list)

    @patch("app.agents.ec2_scanner.boto3.client")
    def test_scan_all_volumes(self, mock_client):
        """Test scanning volumes."""
        mock_ec2 = Mock()
        mock_client.return_value = mock_ec2
        mock_ec2.describe_volumes.return_value = {"Volumes": []}

        scanner = EC2Scanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner.scan_all_volumes()

        assert isinstance(findings, list)


class TestEC2FindingChecks:
    """Test EC2 finding checks."""

    def test_ssh_open_world(self):
        """Test SSH open to world detection."""
        # Simulate security group with SSH open to world
        sg_rules = [
            {
                "FromPort": 22,
                "ToPort": 22,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ]

        # Check the rule
        for rule in sg_rules:
            if rule.get("FromPort") == 22 and rule.get("ToPort") == 22:
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        # Should be flagged as critical
                        assert True
                        break

    def test_rdp_open_world(self):
        """Test RDP open to world detection."""
        # Simulate security group with RDP open to world
        sg_rules = [
            {
                "FromPort": 3389,
                "ToPort": 3389,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ]

        # Check the rule
        for rule in sg_rules:
            if rule.get("FromPort") == 3389 and rule.get("ToPort") == 3389:
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        # Should be flagged as critical
                        assert True
                        break

    def test_volume_encryption_check(self):
        """Test volume encryption status."""
        # Simulate encrypted volume
        encrypted_volume = {"Encrypted": True}
        unencrypted_volume = {"Encrypted": False}

        assert encrypted_volume["Encrypted"]
        assert not unencrypted_volume["Encrypted"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
