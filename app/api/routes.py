"""FastAPI routes for Holocron Sentinel API."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid
import logging

from app.core.session_manager import FileSessionManager
from app.security.anonymization import lgpd_anonymize

# Import agents
from app.agents.audit_agent import AuditAgent
from app.agents.s3_scanner import S3Scanner
from app.agents.iam_scanner import IAMScanner
from app.agents.ec2_scanner import EC2Scanner
from app.agents.security_group_scanner import SecurityGroupScanner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Holocron Sentinel API"])


# Pydantic models
class AuditRequest(BaseModel):
    """Request to start an audit."""

    tenant_id: str
    scanners: Optional[List[str]] = None
    region: Optional[str] = "us-east-1"
    job_id: Optional[str] = None


class AuditResponse(BaseModel):
    """Response for audit job."""

    job_id: str
    tenant_id: str
    status: str
    scanners: List[str]
    timestamp: str


class ScanRequest(BaseModel):
    """Request to run a specific scanner."""

    tenant_id: str
    scanner: str
    region: Optional[str] = "us-east-1"
    resource_id: Optional[str] = None  # For specific resource scans


class ScanResponse(BaseModel):
    """Response for scan results."""

    tenant_id: str
    scanner: str
    findings_count: int
    findings: List[Dict[str, Any]]
    summary: Dict[str, Any]


class ScannersListResponse(BaseModel):
    """Response for available scanners."""

    scanners: List[Dict[str, str]]


# Available scanners
AVAILABLE_SCANNERS = {
    "s3": "S3 Security Scanner - Checks Block Public Access, bucket policies, encryption",
    "iam": "IAM Security Scanner - Checks MFA, access keys, privilege escalation",
    "ec2": "EC2 Security Scanner - Checks SSH/RDP access, volumes, encryption",
    "security_group": "Security Group Scanner - Checks for dangerous port rules",
}


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Holocron Sentinel V2"}


# List available scanners
@router.get("/scanners", response_model=ScannersListResponse)
async def list_scanners():
    """List available scanners."""
    return {
        "scanners": [
            {"id": key, "name": key, "description": value}
            for key, value in AVAILABLE_SCANNERS.items()
        ]
    }


# Start audit job
@router.post("/audit", response_model=AuditResponse)
async def start_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """
    Start an audit job for a tenant.

    Runs all specified scanners and aggregates findings.
    """
    try:
        # Create audit agent
        agent = AuditAgent(tenant_id=request.tenant_id, region=request.region)

        # Start audit
        job_id = request.job_id or str(uuid.uuid4())[:8]
        result = agent.start_audit(scanners=request.scanners, job_id=job_id)

        return AuditResponse(
            job_id=result["job_id"],
            tenant_id=result["tenant_id"],
            status=result["status"],
            scanners=result["scanners"],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.error(f"Failed to start audit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start audit: {str(e)}")


# Get audit results
@router.get("/audit/{job_id}")
async def get_audit_results(job_id: str, tenant_id: str):
    """
    Get audit job results.

    Args:
        job_id: The job ID returned from /api/v1/audit
        tenant_id: The tenant ID (for authorization)
    """
    try:
        # Create audit agent
        agent = AuditAgent(tenant_id=tenant_id)

        # Get job status
        result = agent.get_job_status(job_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Audit job {job_id} not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


# Run specific scanner
@router.post("/scanners/scan", response_model=ScanResponse)
async def run_scanner(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Run a specific scanner.

    Args:
        scanner: One of s3, iam, ec2, security_group
        resource_id: Optional specific resource ID to scan
    """
    try:
        scanner_class = None
        if request.scanner == "s3":
            scanner_class = S3Scanner
        elif request.scanner == "iam":
            scanner_class = IAMScanner
        elif request.scanner == "ec2":
            scanner_class = EC2Scanner
        elif request.scanner == "security_group":
            scanner_class = SecurityGroupScanner
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scanner. Available: {list(AVAILABLE_SCANNERS.keys())}",
            )

        # Create scanner
        scanner = scanner_class(tenant_id=request.tenant_id, region=request.region)

        # Run scan
        if request.resource_id:
            # Scan specific resource
            if request.scanner == "s3":
                findings = scanner.scan_bucket(request.resource_id)
            elif request.scanner == "ec2":
                findings = scanner._scan_instance(request.resource_id, {})
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Resource-specific scanning not supported for {request.scanner}",
                )
        else:
            # Scan all resources
            if request.scanner == "s3":
                findings = scanner.scan_all_buckets()
            elif request.scanner == "iam":
                findings = scanner.scan_all_users()
                findings.extend(scanner.scan_all_roles())
            elif request.scanner == "ec2":
                findings = scanner.scan_all_instances()
                findings.extend(scanner.scan_all_volumes())
            elif request.scanner == "security_group":
                findings = scanner.scan_all_security_groups()

        # Save results
        scanner.save_scan_results()

        # Get summary
        summary = getattr(scanner, "get_findings_summary", lambda: {})()

        # Anonymize findings for LGPD
        anonymized_findings = lgpd_anonymize({"findings": findings})["findings"]

        return ScanResponse(
            tenant_id=request.tenant_id,
            scanner=request.scanner,
            findings_count=len(anonymized_findings),
            findings=anonymized_findings,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run scanner: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run scanner: {str(e)}")


# Get scanner results by ID
@router.get("/scanners/{scanner}/results/{result_id}")
async def get_scanner_results(scanner: str, result_id: str, tenant_id: str):
    """
    Get results from a specific scan.

    Args:
        scanner: The scanner name
        result_id: The result ID (session ID)
        tenant_id: The tenant ID
    """
    try:
        session_manager = FileSessionManager()

        # Get session key
        session_key = f"{scanner}_scan_{tenant_id}"
        if result_id != "current":
            session_key = f"{scanner}_scan_{result_id}"

        results = session_manager.get_session(session_key)

        if not results:
            raise HTTPException(
                status_code=404, detail=f"Results for {scanner} scan not found"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scanner results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


# Get summary
@router.get("/summary/{tenant_id}")
async def get_tenant_summary(tenant_id: str, region: str = "us-east-1"):
    """
    Get aggregated security summary for a tenant.

    Returns:
        - Total findings by severity
        - Last scan timestamp
        - Critical findings count
    """
    try:
        # Create agent
        agent = AuditAgent(tenant_id=tenant_id, region=region)

        # List jobs
        jobs = agent.list_jobs()

        if not jobs:
            return {
                "tenant_id": tenant_id,
                "last_scan": None,
                "total_findings": 0,
                "critical_findings": 0,
                "scanners_used": [],
            }

        # Get most recent completed job
        completed_jobs = [j for j in jobs if j["status"] == "completed"]
        if not completed_jobs:
            return {
                "tenant_id": tenant_id,
                "last_scan": None,
                "total_findings": 0,
                "critical_findings": 0,
                "scanners_used": [],
            }

        latest_job = max(completed_jobs, key=lambda x: x.get("start_time", ""))

        return {
            "tenant_id": tenant_id,
            "last_scan": latest_job.get("end_time"),
            "total_findings": latest_job.get("findings_count", 0),
            "critical_findings": latest_job.get("findings_by_severity", {}).get(
                "critical", 0
            ),
            "scanners_used": latest_job.get("scanners", []),
        }

    except Exception as e:
        logger.error(f"Failed to get tenant summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


# Get all scanners status
@router.get("/scanners/status")
async def get_scanners_status(tenant_id: str, region: str = "us-east-1"):
    """
    Check status of all scanners.

    Returns:
        Status for each scanner (ready, error)
    """
    status = {}

    for scanner_name in AVAILABLE_SCANNERS.keys():
        try:
            scanner_class = None
            if scanner_name == "s3":
                scanner_class = S3Scanner
            elif scanner_name == "iam":
                scanner_class = IAMScanner
            elif scanner_name == "ec2":
                scanner_class = EC2Scanner
            elif scanner_name == "security_group":
                scanner_class = SecurityGroupScanner

            if scanner_class:
                scanner = scanner_class(tenant_id=tenant_id, region=region)
                # Test connection
                if scanner_name == "s3":
                    scanner.s3_client.list_buckets()
                elif scanner_name == "iam":
                    scanner.iam_client.list_users()
                elif scanner_name == "ec2":
                    scanner.ec2_client.describe_instances()

                status[scanner_name] = {"status": "ready", "error": None}
        except Exception as e:
            status[scanner_name] = {"status": "error", "error": str(e)}

    return status
