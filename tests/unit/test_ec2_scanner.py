"""Unit tests for EC2 Scanner."""

import os
import sys
from unittest.mock import Mock, patch

import pytest

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
        scanner = EC2Scanner(tenant_id="test_tenant")
        scanner._ec2_client = Mock(
            describe_instances=Mock(
                return_value={
                    "Reservations": [
                        {"Instances": [{"SecurityGroups": [{"GroupId": "sg-123"}]}]}
                    ]
                }
            )
        )
        scanner._get_security_group_rules = Mock(
            return_value=[
                {
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }
            ]
        )

        findings = scanner._check_ssh_open_to_world("i-12345678", "test-instance")

        assert len(findings) == 1
        assert findings[0]["check_name"] == "security_group.ssh_world"
        assert findings[0]["severity"] == "critical"
        assert findings[0]["status"] == "fail"

    def test_rdp_open_world(self):
        """Test RDP open to world detection."""
        scanner = EC2Scanner(tenant_id="test_tenant")
        scanner._ec2_client = Mock(
            describe_instances=Mock(
                return_value={
                    "Reservations": [
                        {"Instances": [{"SecurityGroups": [{"GroupId": "sg-123"}]}]}
                    ]
                }
            )
        )
        scanner._get_security_group_rules = Mock(
            return_value=[
                {
                    "FromPort": 3389,
                    "ToPort": 3389,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }
            ]
        )

        findings = scanner._check_rdp_open_to_world("i-12345678", "test-instance")

        assert len(findings) == 1
        assert findings[0]["check_name"] == "security_group.rdp_world"
        assert findings[0]["severity"] == "critical"
        assert findings[0]["status"] == "fail"

    def test_volume_encryption_check(self):
        """Test volume encryption status."""
        scanner = EC2Scanner(tenant_id="test_tenant")
        encrypted = scanner._check_volume_encryption(
            "vol-encrypted", "encrypted", {"Encrypted": True}
        )
        unencrypted = scanner._check_volume_encryption(
            "vol-unencrypted", "unencrypted", {"Encrypted": False}
        )

        assert encrypted[0]["check_name"] == "volume.encrypted"
        assert encrypted[0]["status"] == "pass"
        assert unencrypted[0]["check_name"] == "volume.unencrypted"
        assert unencrypted[0]["severity"] == "high"
        assert unencrypted[0]["status"] == "fail"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
