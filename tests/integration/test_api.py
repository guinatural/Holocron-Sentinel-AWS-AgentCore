"""Offline integration tests for API endpoints."""

import asyncio
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import Mock

import httpx

from app.agents.audit_agent import AuditAgent
from app.api import routes
from app.api.main import app


def request(method, path, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


class StubScanner:
    def __init__(self, tenant_id, region="us-east-1"):
        self.tenant_id = tenant_id
        self.region = region

    def scan_all_buckets(self):
        return [
            {
                "check_name": "bucket.encryption",
                "status": "fail",
                "severity": "critical",
                "description": "Bucket encryption is disabled",
            }
        ]

    def save_scan_results(self):
        return True

    def get_findings_summary(self):
        return {"critical": 1}


class StubBedrockClient:
    instances: ClassVar[list] = []

    def __init__(self, region_name):
        self.calls = []
        self.instances.append(self)

    def invoke_for_use_case(self, **kwargs):
        self.calls.append(kwargs)
        return "Relatório executivo de teste."


class TestAPIEndpoints:
    def test_health_check(self):
        response = request("GET", "/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "Holocron Sentinel V2",
        }

    def test_root_and_status_endpoints(self):
        root_response = request("GET", "/")
        status_response = request("GET", "/status")

        assert root_response.status_code == 200
        assert root_response.json()["version"] == "2.0.0"
        assert root_response.json()["docs"] == "/docs"
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "running"

    def test_list_scanners(self):
        response = request("GET", "/api/v1/scanners")

        assert response.status_code == 200
        scanners = response.json()["scanners"]
        assert {scanner["id"] for scanner in scanners} == {
            "s3",
            "iam",
            "ec2",
            "security_group",
        }
        assert all(
            {"id", "name", "description"} <= scanner.keys() for scanner in scanners
        )


class TestAuditEndpoints:
    def test_start_get_results_and_summary_across_requests(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(AuditAgent, "SCANNERS", {"s3": StubScanner})
        monkeypatch.setattr("app.agents.audit_agent.BedrockClient", StubBedrockClient)
        StubBedrockClient.instances.clear()

        started = request(
            "POST",
            "/api/v1/audit",
            json={
                "tenant_id": "tenant-a",
                "scanners": ["s3"],
                "job_id": "local-job-1",
            },
        )

        assert started.status_code == 200
        start_data = started.json()
        assert start_data["job_id"] == "local-job-1"
        assert start_data["tenant_id"] == "tenant-a"
        assert start_data["status"] == "completed"
        assert start_data["scanners"] == ["s3"]
        assert len(StubBedrockClient.instances) == 1
        assert (
            StubBedrockClient.instances[0].calls[0]["use_case"] == "detailed_analysis"
        )

        results = request(
            "GET", "/api/v1/audit/local-job-1", params={"tenant_id": "tenant-a"}
        )
        assert results.status_code == 200
        result_data = results.json()
        assert result_data["status"] == "completed"
        assert result_data["findings_count"] == 1
        assert result_data["findings_by_severity"] == {"critical": 1}
        assert result_data["results"]["s3"]["findings"][0]["check_name"] == (
            "bucket.encryption"
        )
        assert (
            result_data["results"]["report"]["executive_summary"]
            == "Relatório executivo de teste."
        )

        summary = request("GET", "/api/v1/summary/tenant-a")
        assert summary.status_code == 200
        assert summary.json()["total_findings"] == 1
        assert summary.json()["critical_findings"] == 1
        assert summary.json()["scanners_used"] == ["s3"]

        other_tenant = request(
            "GET", "/api/v1/audit/local-job-1", params={"tenant_id": "tenant-b"}
        )
        assert other_tenant.status_code == 404
        assert request("GET", "/api/v1/summary/tenant-b").json()["total_findings"] == 0

    def test_get_audit_results_returns_404_for_missing_job(self):
        response = request(
            "GET",
            "/api/v1/audit/nonexistent-job",
            params={"tenant_id": "missing-tenant"},
        )
        assert response.status_code == 404


class TestScannerEndpoints:
    def test_run_s3_scanner_returns_findings(self, monkeypatch):
        monkeypatch.setattr(routes, "S3Scanner", StubScanner)

        response = request(
            "POST",
            "/api/v1/scanners/scan",
            json={"tenant_id": "tenant-a", "scanner": "s3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scanner"] == "s3"
        assert data["findings_count"] == 1
        assert data["findings"][0]["check_name"] == "bucket.encryption"
        assert data["summary"] == {"critical": 1}

    def test_run_invalid_scanner_returns_400(self):
        response = request(
            "POST",
            "/api/v1/scanners/scan",
            json={"tenant_id": "tenant-a", "scanner": "invalid_scanner"},
        )

        assert response.status_code == 400
        assert "Invalid scanner" in response.json()["detail"]

    def test_scanner_status_uses_local_stubs(self, monkeypatch):
        monkeypatch.setattr(
            routes,
            "S3Scanner",
            lambda **kwargs: SimpleNamespace(s3_client=Mock(list_buckets=Mock())),
        )
        monkeypatch.setattr(
            routes,
            "IAMScanner",
            lambda **kwargs: SimpleNamespace(iam_client=Mock(list_users=Mock())),
        )
        monkeypatch.setattr(
            routes,
            "EC2Scanner",
            lambda **kwargs: SimpleNamespace(
                ec2_client=Mock(describe_instances=Mock())
            ),
        )
        monkeypatch.setattr(routes, "SecurityGroupScanner", lambda **kwargs: object())

        response = request(
            "GET", "/api/v1/scanners/status", params={"tenant_id": "tenant-a"}
        )
        assert response.status_code == 200
        assert {item["status"] for item in response.json().values()} == {"ready"}


class TestCORS:
    def test_cors_headers(self):
        response = request(
            "OPTIONS",
            "/health",
            headers={
                "Origin": "http://testserver",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Requested-With",
            },
        )

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
