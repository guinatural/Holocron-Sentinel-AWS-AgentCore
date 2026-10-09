"""Unit tests for IAM Scanner."""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.iam_scanner import IAMScanner


class TestIAMScanner:
    """Test IAM scanner functionality."""

    def test_init(self):
        """Test scanner initialization."""
        scanner = IAMScanner(tenant_id="test_tenant", region="us-east-1")

        assert scanner.tenant_id == "test_tenant"
        assert scanner.region == "us-east-1"
        assert scanner.findings == []

    @patch("app.agents.iam_scanner.boto3.client")
    def test_iam_client_creation(self, mock_client):
        """Test IAM client creation."""
        mock_iam = Mock()
        mock_client.return_value = mock_iam

        scanner = IAMScanner(tenant_id="test_tenant", region="us-east-1")
        _ = scanner.iam_client

        mock_client.assert_called_once_with("iam")

    @patch("app.agents.iam_scanner.boto3.client")
    def test_scan_all_users_empty(self, mock_client):
        """Test scanning when no users exist."""
        mock_iam = Mock()
        mock_client.return_value = mock_iam
        mock_iam.list_users.return_value = {"Users": []}

        scanner = IAMScanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner.scan_all_users()

        assert isinstance(findings, list)

    @patch("app.agents.iam_scanner.boto3.client")
    def test_check_mfa_enabled(self, mock_client):
        """Test MFA check when enabled."""
        mock_iam = Mock()
        mock_client.return_value = mock_iam
        mock_iam.list_mfa_devices.return_value = {
            "MFADevices": [{"MFADeviceName": "mfa-device"}]
        }

        scanner = IAMScanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner._check_mfa_enabled(
            "test-user", "arn:aws:iam::123456:user/test-user"
        )

        assert len(findings) == 1
        assert findings[0]["status"] == "pass"
        assert "mfa" in findings[0]["check_name"]

    @patch("app.agents.iam_scanner.boto3.client")
    def test_check_mfa_disabled(self, mock_client):
        """Test MFA check when disabled."""
        mock_iam = Mock()
        mock_client.return_value = mock_iam
        mock_iam.list_mfa_devices.return_value = {"MFADevices": []}

        scanner = IAMScanner(tenant_id="test_tenant", region="us-east-1")
        findings = scanner._check_mfa_enabled(
            "test-user", "arn:aws:iam::123456:user/test-user"
        )

        assert len(findings) == 1
        assert findings[0]["status"] == "fail"
        assert findings[0]["severity"] == "high"


class TestIAMFindings:
    """Test IAM finding structures."""

    def test_finding_structure(self):
        """Test finding has required fields."""
        finding = {
            "finding_id": "iam-test-user-mfa-disabled",
            "severity": "high",
            "category": "security",
            "resource_type": "user",
            "resource_name": "test-user",
            "check_name": "mfa.disabled",
            "status": "fail",
            "description": "MFA is not enabled",
            "remediation": "Enable MFA",
        }

        assert finding["severity"] in ["critical", "high", "medium", "low", "info"]
        assert finding["category"] in [
            "security",
            "compliance",
            "privilege_escalation",
            "error",
        ]
        assert finding["status"] in ["pass", "fail", "warning", "error"]

    def test_lgpd_compliance(self):
        """Test findings are anonymized."""
        from app.security.anonymization import lgpd_anonymize

        findings = [{"description": "User john@example.com has issues"}]
        anonymized = lgpd_anonymize({"findings": findings})

        assert "john@example.com" not in anonymized["findings"][0]["description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
