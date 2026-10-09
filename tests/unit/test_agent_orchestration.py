"""Unit tests for Agent orchestration."""

import os
import sys
from unittest.mock import Mock

import pytest

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.audit_agent import AuditAgent, AuditJob


class TestAuditAgent:
    """Test Audit Agent orchestration."""

    def test_init(self):
        """Test agent initialization."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")

        assert agent.tenant_id == "test_tenant"
        assert agent.region == "us-east-1"
        assert agent.jobs == {}

    def test_start_audit_default_scanners(self, monkeypatch):
        """Test starting audit with default scanners."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        agent.session_manager.save_session = Mock(return_value=True)
        scanner = Mock()
        scanner.scan_all_buckets.return_value = []
        scanner.scan_all_users.return_value = []
        scanner.scan_all_roles.return_value = []
        scanner.scan_all_instances.return_value = []
        scanner.scan_all_volumes.return_value = []
        scanner.scan_all_security_groups.return_value = []
        scanner.save_scan_results.return_value = True
        monkeypatch.setattr(
            AuditAgent,
            "SCANNERS",
            {name: Mock(return_value=scanner) for name in AuditAgent.SCANNERS},
        )
        agent.bedrock_client.invoke_for_use_case = Mock(return_value="Relatório")

        result = agent.start_audit(job_id="test123")

        assert result["job_id"] == "test123"
        assert result["tenant_id"] == "test_tenant"
        assert result["status"] == "completed"
        assert result["scanners"] == ["s3", "iam", "ec2", "security_group"]
        assert result["findings_count"] == 0
        assert result["results"]["report"]["executive_summary"] == "Relatório"
        assert scanner.scan_all_buckets.called
        assert scanner.scan_all_users.called
        assert scanner.scan_all_roles.called
        assert scanner.scan_all_instances.called
        assert scanner.scan_all_volumes.called
        assert scanner.scan_all_security_groups.called
        agent.bedrock_client.invoke_for_use_case.assert_called_once()

    def test_start_audit_specific_scanners(self, monkeypatch):
        """Test starting audit with specific scanners."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        agent.session_manager.save_session = Mock(return_value=True)
        scanner = Mock()
        scanner.scan_all_buckets.return_value = [
            {"severity": "high", "status": "fail", "check_name": "bucket.public"}
        ]
        scanner.save_scan_results.return_value = True
        monkeypatch.setattr(AuditAgent, "SCANNERS", {"s3": Mock(return_value=scanner)})
        agent.bedrock_client.invoke_for_use_case = Mock(return_value="Análise real")

        result = agent.start_audit(scanners=["s3"], job_id="test456")

        assert result["status"] == "completed"
        assert result["scanners"] == ["s3"]
        assert result["findings_count"] == 1
        assert result["findings_by_severity"] == {"high": 1}
        assert result["results"]["s3"]["findings"][0]["check_name"] == "bucket.public"
        assert result["results"]["report"]["executive_summary"] == "Análise real"

    def test_available_scanners(self):
        """Test available scanners list."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")

        assert "s3" in agent.SCANNERS
        assert "iam" in agent.SCANNERS
        assert "ec2" in agent.SCANNERS
        assert "security_group" in agent.SCANNERS

    def test_job_status_tracking(self):
        """Test job status tracking."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")

        # Create a mock job
        job = AuditJob(
            job_id="test123", tenant_id="test_tenant", status="pending", scanners=["s3"]
        )

        agent.jobs["test123"] = job

        # Get job status
        result = agent.get_job_status("test123")

        assert result["job_id"] == "test123"
        assert result["status"] == "pending"

    def test_list_jobs(self):
        """Test listing jobs."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")

        # Add mock jobs
        job1 = AuditJob(
            job_id="job1", tenant_id="test_tenant", status="completed", scanners=["s3"]
        )
        job2 = AuditJob(
            job_id="job2", tenant_id="test_tenant", status="running", scanners=["iam"]
        )

        agent.jobs["job1"] = job1
        agent.jobs["job2"] = job2

        jobs = agent.list_jobs()

        assert len(jobs) == 2
        assert jobs[0]["job_id"] in ["job1", "job2"]
        assert jobs[1]["job_id"] in ["job1", "job2"]


class TestAuditJobDataclass:
    """Test AuditJob dataclass."""

    def test_job_creation(self):
        """Test creating a job."""
        job = AuditJob(
            job_id="test123",
            tenant_id="tenant_1",
            status="pending",
            scanners=["s3", "iam"],
        )

        assert job.job_id == "test123"
        assert job.tenant_id == "tenant_1"
        assert job.status == "pending"
        assert "s3" in job.scanners
        assert "iam" in job.scanners

    def test_job_with_results(self):
        """Test job with results."""
        job = AuditJob(
            job_id="test456",
            tenant_id="tenant_2",
            status="completed",
            scanners=["s3"],
            findings_count=10,
            findings_by_severity={"critical": 1, "high": 2, "medium": 3, "low": 4},
            results={"s3": {"findings": [], "summary": {}}},
        )

        assert job.findings_count == 10
        assert job.findings_by_severity["critical"] == 1
        assert "s3" in job.results


class TestAgentOrchestration:
    """Test agent orchestration scenarios."""

    def test_multi_scanner_execution(self, monkeypatch):
        """Test running multiple scanners."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        agent.session_manager.save_session = Mock(return_value=True)
        assert len(agent.SCANNERS) == 4
        scanner = Mock()
        scanner.scan_all_buckets.return_value = []
        scanner.scan_all_users.return_value = []
        scanner.scan_all_roles.return_value = []
        scanner.scan_all_instances.return_value = []
        scanner.scan_all_volumes.return_value = []
        scanner.scan_all_security_groups.return_value = []
        scanner.save_scan_results.return_value = True
        monkeypatch.setattr(
            AuditAgent,
            "SCANNERS",
            {name: Mock(return_value=scanner) for name in AuditAgent.SCANNERS},
        )
        agent.bedrock_client.invoke_for_use_case = Mock(return_value="Relatório")

        result = agent.start_audit(scanners=list(AuditAgent.SCANNERS))

        assert result["status"] == "completed"
        assert result["scanners"] == list(AuditAgent.SCANNERS)
        assert all(
            entry["summary"] == {"pass": 0, "fail": 0, "warning": 0, "error": 0}
            for name, entry in result["results"].items()
            if name != "report"
        )

    def test_single_scanner_execution(self, monkeypatch):
        """Test running a single scanner."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        agent.session_manager.save_session = Mock(return_value=True)
        scanner = Mock()
        scanner.scan_all_buckets.return_value = []
        scanner.save_scan_results.return_value = True
        monkeypatch.setattr(AuditAgent, "SCANNERS", {"s3": Mock(return_value=scanner)})
        agent.bedrock_client.invoke_for_use_case = Mock(return_value="Relatório")

        result = agent.start_audit(scanners=["s3"], job_id="single-scanner")

        assert result["status"] == "completed"
        assert result["scanners"] == ["s3"]
        assert result["results"]["s3"]["findings"] == []
        scanner.scan_all_buckets.assert_called_once()

    def test_lgpd_compliance_in_agent(self):
        """Test LGPD compliance in agent findings."""
        from app.security.anonymization import lgpd_anonymize

        # Test anonymization
        findings = [{"description": "User john@example.com has issues"}]
        anonymized = lgpd_anonymize({"findings": findings})

        assert "john@example.com" not in anonymized["findings"][0]["description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
