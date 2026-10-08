"""Audit Agent - Orchestrates scanning, coordinates tools, delivers reports."""
import boto3
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.aws.bedrock import BedrockClient
from app.core.session_manager import FileSessionManager
from app.security.anonymization import lgpd_anonymize

# Import scanners
from app.agents.s3_scanner import S3Scanner
from app.agents.iam_scanner import IAMScanner
from app.agents.ec2_scanner import EC2Scanner
from app.agents.security_group_scanner import SecurityGroupScanner

logger = logging.getLogger(__name__)


@dataclass
class AuditJob:
    """Audit job record."""
    job_id: str
    tenant_id: str
    status: str  # pending, running, completed, failed
    scanners: List[str]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    findings_count: int = 0
    findings_by_severity: Dict[str, int] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class AuditAgent:
    """
    Audit Agent - Orchestrates security scanning and report generation.
    
    Features:
    - Multi-tenant isolation
    - Scanner coordination
    - Finding aggregation
    - Report generation
    - LGPD compliance (anonymization)
    """
    
    # Available scanners
    SCANNERS = {
        's3': S3Scanner,
        'iam': IAMScanner,
        'ec2': EC2Scanner,
        'security_group': SecurityGroupScanner,
    }
    
    def __init__(self, tenant_id: str, region: str = 'us-east-1'):
        """
        Initialize Audit Agent for a specific tenant.
        
        Args:
            tenant_id: Unique tenant identifier for isolation
            region: AWS region to scan
        """
        self.tenant_id = tenant_id
        self.region = region
        self.session_manager = FileSessionManager()
        self.bedrock_client = BedrockClient(region_name=region)
        self.jobs: Dict[str, AuditJob] = {}
        
    def start_audit(self, scanners: List[str] = None, job_id: str = None) -> Dict[str, Any]:
        """
        Start an audit job.
        
        Args:
            scanners: List of scanner names to run. If None, runs all.
            job_id: Optional job ID for tracking
            
        Returns:
            Job metadata
        """
        # Generate job ID if not provided
        if not job_id:
            import uuid
            job_id = str(uuid.uuid4())[:8]
        
        # Default to all scanners
        if not scanners:
            scanners = list(self.SCANNERS.keys())
        
        # Validate scanners
        invalid_scanners = [s for s in scanners if s not in self.SCANNERS]
        if invalid_scanners:
            logger.warning(f"Invalid scanners: {invalid_scanners}. Available: {list(self.SCANNERS.keys())}")
            scanners = [s for s in scanners if s in self.SCANNERS]
        
        # Create job record
        job = AuditJob(
            job_id=job_id,
            tenant_id=self.tenant_id,
            status='pending',
            scanners=scanners
        )
        self.jobs[job_id] = job
        
        # Run audit
        return self._run_audit(job_id)
    
    def _run_audit(self, job_id: str) -> Dict[str, Any]:
        """Execute the audit job."""
        job = self.jobs[job_id]
        job.start_time = datetime.utcnow().isoformat()
        job.status = 'running'
        
        all_findings = []
        results = {}
        
        try:
            # Run each scanner
            for scanner_name in job.scanners:
                logger.info(f"Running scanner: {scanner_name}")
                
                scanner_class = self.SCANNERS[scanner_name]
                scanner = scanner_class(tenant_id=self.tenant_id, region=self.region)
                
                # Run the appropriate scan method
                if scanner_name == 's3':
                    findings = scanner.scan_all_buckets()
                elif scanner_name == 'iam':
                    findings = scanner.scan_all_users()
                    findings.extend(scanner.scan_all_roles())
                elif scanner_name == 'ec2':
                    findings = scanner.scan_all_instances()
                    findings.extend(scanner.scan_all_volumes())
                elif scanner_name == 'security_group':
                    findings = scanner.scan_all_security_groups()
                else:
                    findings = []
                
                # Store results
                results[scanner_name] = {
                    'findings': findings,
                    'summary': self._get_summary_from_findings(findings)
                }
                
                # Aggregate findings
                all_findings.extend(findings)
                
                # Save scanner results
                scanner.save_scan_results()
            
            # Update job
            job.status = 'completed'
            job.end_time = datetime.utcnow().isoformat()
            job.findings_count = len(all_findings)
            job.findings_by_severity = self._count_by_severity(all_findings)
            job.results = results
            
            # Save job results
            self._save_job_results(job)
            
            # Generate summary report
            report = self._generate_report(job, all_findings)
            job.results['report'] = report
            
            logger.info(f"Audit job {job_id} completed with {len(all_findings)} findings")
            
        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            job.end_time = datetime.utcnow().isoformat()
            logger.error(f"Audit job {job_id} failed: {e}")
        
        return self._get_job_output(job)
    
    def _get_summary_from_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary from findings."""
        summary = {'pass': 0, 'fail': 0, 'warning': 0, 'error': 0}
        
        for finding in findings:
            status = finding.get('status', 'unknown')
            summary[status] = summary.get(status, 0) + 1
        
        return summary
    
    def _count_by_severity(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by severity."""
        severity_counts = {}
        
        for finding in findings:
            severity = finding.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
    
    def _generate_report(self, job: AuditJob, all_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate audit report using Bedrock."""
        # Build summary
        total_findings = len(all_findings)
        by_severity = self._count_by_severity(all_findings)
        
        # Build prompt for Bedrock
        prompt = f"""Você é um auditor de segurança AWS especializado em LGPD.

RESUMO DA AUDITORIA:
- Tenant: {self.tenant_id}
- Job ID: {job.job_id}
- Total de falhas: {total_findings}
- Por severidade:
{self._format_severity_breakdown(by_severity)}

FALHAS CRÍTICAS E ALTA SEVERIDADE:
{self._format_critical_findings(all_findings)}

SUGESTÕES DE AÇÃO:
1. Priorize correções para falhas CRÍTICAS e ALTA severidade
2. Revise políticas de segurança e ACLs
3. Habilite criptografia em recursos não criptografados
4. Remova acesso público desnecessário
5. Ative logging de acesso

Forneça um relatório executivo em português com:
1. Visão geral do estado de segurança
2. Principais riscos identificados
3. Recomendações prioritárias
4. Estimativa de esforço de correção

Responda em português brasileiro com linguagem clara para gestores."""
        
        try:
            # Use Sonnet for detailed analysis
            self.bedrock_client.set_model('sonnet')
            report_text = self.bedrock_client.invoke_model(
                prompt=prompt,
                system_prompt="Você é um DPO (Data Protection Officer) especializado em segurança AWS e conformidade LGPD.",
                use_case='detailed_analysis'
            )
            
            return {
                'executive_summary': report_text,
                'generated_at': datetime.utcnow().isoformat(),
                'findings_count': total_findings,
                'by_severity': by_severity,
                'scanners_used': job.scanners
            }
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            # Return fallback report
            return {
                'executive_summary': f"Auditoria concluída com {total_findings} falhas. Consulte detalhes nos resultados.",
                'generated_at': datetime.utcnow().isoformat(),
                'findings_count': total_findings,
                'by_severity': by_severity,
                'scanners_used': job.scanners,
                'error': str(e)
            }
    
    def _format_severity_breakdown(self, by_severity: Dict[str, int]) -> str:
        """Format severity breakdown for prompt."""
        lines = []
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_severity.get(severity, 0)
            if count > 0:
                lines.append(f"  - {severity.upper()}: {count}")
        return '\n'.join(lines) if lines else "  - Nenhuma falha encontrada"
    
    def _format_critical_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Format critical findings for prompt."""
        critical = [f for f in findings if f.get('severity') in ['critical', 'high']]
        
        if not critical:
            return "Nenhuma falha crítica ou de alta severidade encontrada."
        
        lines = []
        for finding in critical[:10]:  # Limit to 10
            lines.append(f"- [{finding.get('severity', 'unknown').upper()}] {finding.get('check_name', 'unknown')}: {finding.get('description', 'No description')}")
        
        if len(critical) > 10:
            lines.append(f"...e mais {len(critical) - 10} falhas")
        
        return '\n'.join(lines)
    
    def _save_job_results(self, job: AuditJob) -> bool:
        """Save job results to session manager."""
        job_data = {
            'job_id': job.job_id,
            'tenant_id': job.tenant_id,
            'status': job.status,
            'start_time': job.start_time,
            'end_time': job.end_time,
            'findings_count': job.findings_count,
            'findings_by_severity': job.findings_by_severity,
            'results': job.results,
            'error': job.error,
            'timestamp': job.timestamp
        }
        
        return self.session_manager.save_session(f"audit_job_{job.job_id}", job_data)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get audit job status."""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return self._get_job_output(job)
    
    def _get_job_output(self, job: AuditJob) -> Dict[str, Any]:
        """Get job output."""
        return {
            'job_id': job.job_id,
            'tenant_id': job.tenant_id,
            'status': job.status,
            'scanners': job.scanners,
            'start_time': job.start_time,
            'end_time': job.end_time,
            'findings_count': job.findings_count,
            'findings_by_severity': job.findings_by_severity,
            'results': job.results,
            'error': job.error,
            'timestamp': job.timestamp
        }
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all audit jobs for this tenant."""
        return [self._get_job_output(job) for job in self.jobs.values()]
    
    def get_findings(self, job_id: str, severity_filter: str = None) -> List[Dict[str, Any]]:
        """Get findings from a job."""
        if job_id not in self.jobs:
            return []
        
        job = self.jobs[job_id]
        all_findings = []
        
        for scanner_name, scanner_results in job.results.items():
            if scanner_name == 'report':
                continue
            all_findings.extend(scanner_results.get('findings', []))
        
        if severity_filter:
            all_findings = [f for f in all_findings if f.get('severity') == severity_filter]
        
        return all_findings
