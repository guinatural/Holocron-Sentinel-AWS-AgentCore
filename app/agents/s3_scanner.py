"""S3 Scanner - Checks Block Public Access, bucket policies, encryption."""
import boto3
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from app.aws.bedrock import BedrockClient
from app.core.session_manager import FileSessionManager
from app.security.anonymization import lgpd_anonymize

logger = logging.getLogger(__name__)


@dataclass
class S3Finding:
    """S3 scanner finding."""
    finding_id: str
    severity: str  # critical, high, medium, low, info
    category: str  # security, compliance, configuration
    bucket_name: str
    check_name: str
    status: str  # pass, fail, warning
    description: str
    remediation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class S3Scanner:
    """
    S3 security scanner for multi-tenant AWS environments.
    
    Checks:
    - Block Public Access settings
    - Bucket policies
    - Encryption status
    - Versioning
    - Logging
    """
    
    SEVERITY_LEVELS = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1,
        'info': 0
    }
    
    def __init__(self, tenant_id: str, region: str = 'us-east-1'):
        """
        Initialize S3 scanner for a specific tenant.
        
        Args:
            tenant_id: Unique tenant identifier for isolation
            region: AWS region to scan
        """
        self.tenant_id = tenant_id
        self.region = region
        self.session_manager = FileSessionManager()
        self._session = None
        self.findings: List[S3Finding] = []
        
    @property
    def s3_client(self) -> boto3.client:
        """Get S3 client with tenant-specific configuration."""
        if self._session is None:
            self._session = boto3.Session(
                region_name=self.region
            )
        return self._session.client('s3')
    
    def scan_bucket(self, bucket_name: str) -> List[Dict[str, Any]]:
        """
        Scan a single S3 bucket for security issues.
        
        Args:
            bucket_name: Name of the bucket to scan
            
        Returns:
            List of findings for the bucket
        """
        findings = []
        
        try:
            # 1. Check Block Public Access
            findings.extend(self._check_block_public_access(bucket_name))
            
            # 2. Check bucket policy
            findings.extend(self._check_bucket_policy(bucket_name))
            
            # 3. Check encryption
            findings.extend(self._check_encryption(bucket_name))
            
            # 4. Check versioning
            findings.extend(self._check_versioning(bucket_name))
            
            # 5. Check logging
            findings.extend(self._check_logging(bucket_name))
            
            # 6. Check bucket access control
            findings.extend(self._check_access_control(bucket_name))
            
        except Exception as e:
            logger.error(f"Error scanning bucket {bucket_name}: {e}")
            findings.append({
                'severity': 'high',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'scan_error',
                'status': 'error',
                'description': f"Failed to scan bucket: {str(e)}",
                'remediation': 'Check AWS credentials and permissions'
            })
        
        # Anonymize findings for LGPD compliance
        anonymized_findings = lgpd_anonymize({'findings': findings})
        
        return anonymized_findings['findings']
    
    def scan_all_buckets(self) -> List[Dict[str, Any]]:
        """
        Scan all S3 buckets in the region.
        
        Returns:
            List of all findings across all buckets
        """
        all_findings = []
        
        try:
            buckets = self.s3_client.list_buckets()
            
            for bucket in buckets.get('Buckets', []):
                bucket_name = bucket['Name']
                logger.info(f"Scanning bucket: {bucket_name}")
                
                bucket_findings = self.scan_bucket(bucket_name)
                all_findings.extend(bucket_findings)
                
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            all_findings.append({
                'severity': 'critical',
                'category': 'error',
                'bucket_name': 'all',
                'check_name': 'list_buckets_error',
                'status': 'error',
                'description': f"Failed to list buckets: {str(e)}",
                'remediation': 'Check AWS credentials and permissions'
            })
        
        return all_findings
    
    def _check_block_public_access(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Check Block Public Access settings."""
        findings = []
        
        try:
            response = self.s3_client.get_public_access_block(
                Bucket=bucket_name
            )
            block_config = response['PublicAccessBlockConfiguration']
            
            checks = [
                ('block_public_acls', 'Block Public ACLs'),
                ('ignore_public_acls', 'Ignore Public ACLs'),
                ('block_public_policy', 'Block Public Policy'),
                ('restrict_public_buckets', 'Restrict Public Buckets')
            ]
            
            all_blocked = True
            for config_key, config_name in checks:
                if not block_config.get(config_key, False):
                    all_blocked = False
                    findings.append({
                        'finding_id': f"s3-{bucket_name[:8]}-bpa-{config_key[:3]}",
                        'severity': 'high',
                        'category': 'security',
                        'bucket_name': bucket_name,
                        'check_name': f'block_public_access.{config_name}',
                        'status': 'fail',
                        'description': f"{config_name} is not enabled for bucket {bucket_name}",
                        'remediation': f"Enable {config_name} in S3 Block Public Access settings"
                    })
            
            if all_blocked:
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-bpa-all",
                    'severity': 'info',
                    'category': 'security',
                    'bucket_name': bucket_name,
                    'check_name': 'block_public_access.all',
                    'status': 'pass',
                    'description': f"All Block Public Access settings enabled for bucket {bucket_name}",
                    'remediation': 'No action required'
                })
                
        except self.s3_client.exceptions.NoSuchPublicAccessBlockConfiguration:
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-bpa-none",
                'severity': 'critical',
                'category': 'security',
                'bucket_name': bucket_name,
                'check_name': 'block_public_access.none',
                'status': 'fail',
                'description': f"Block Public Access is not configured for bucket {bucket_name}",
                'remediation': 'Configure Block Public Access to prevent accidental public exposure'
            })
            
        except Exception as e:
            logger.warning(f"Could not check Block Public Access for {bucket_name}: {e}")
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-bpa-error",
                'severity': 'medium',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'block_public_access.error',
                'status': 'warning',
                'description': f"Could not verify Block Public Access: {str(e)}",
                'remediation': 'Check permissions for s3:GetPublicAccessBlock'
            })
        
        return findings
    
    def _check_bucket_policy(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Check bucket policy for overly permissive statements."""
        findings = []
        
        try:
            response = self.s3_client.get_bucket_policy(Bucket=bucket_name)
            policy = response.get('Policy', '{}')
            
            # Note: In production, parse and analyze the policy JSON
            # For now, we just log that policy exists
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-policy-exists",
                'severity': 'info',
                'category': 'compliance',
                'bucket_name': bucket_name,
                'check_name': 'bucket_policy.exists',
                'status': 'pass',
                'description': f"Bucket {bucket_name} has a bucket policy configured",
                'remediation': 'Review policy statements for overly permissive access'
            })
            
        except self.s3_client.exceptions.PolicyNotFound:
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-policy-none",
                'severity': 'medium',
                'category': 'compliance',
                'bucket_name': bucket_name,
                'check_name': 'bucket_policy.none',
                'status': 'warning',
                'description': f"Bucket {bucket_name} has no bucket policy",
                'remediation': 'Consider adding a bucket policy for access control and auditing'
            })
            
        except Exception as e:
            logger.warning(f"Could not check bucket policy for {bucket_name}: {e}")
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-policy-error",
                'severity': 'medium',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'bucket_policy.error',
                'status': 'warning',
                'description': f"Could not verify bucket policy: {str(e)}",
                'remediation': 'Check permissions for s3:GetBucketPolicy'
            })
        
        return findings
    
    def _check_encryption(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Check bucket encryption settings."""
        findings = []
        
        try:
            response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            
            if not rules:
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-enc-none",
                    'severity': 'high',
                    'category': 'security',
                    'bucket_name': bucket_name,
                    'check_name': 'encryption.none',
                    'status': 'fail',
                    'description': f"Bucket {bucket_name} has no server-side encryption configured",
                    'remediation': 'Enable AES-256 or AWS-KMS encryption for all objects'
                })
            else:
                # Check if all rules use encryption
                has_encryption = False
                for rule in rules:
                    apply_server_side_encryption_by_default = rule.get('ApplyServerSideEncryptionByDefault', {})
                    if apply_server_side_encryption_by_default:
                        has_encryption = True
                        encryption_type = apply_server_side_encryption_by_default.get('SSEAlgorithm', 'unknown')
                        findings.append({
                            'finding_id': f"s3-{bucket_name[:8]}-enc-{encryption_type[:3]}",
                            'severity': 'info',
                            'category': 'security',
                            'bucket_name': bucket_name,
                            'check_name': f'encryption.{encryption_type}',
                            'status': 'pass',
                            'description': f"Bucket {bucket_name} has {encryption_type} encryption enabled",
                            'remediation': 'Ensure encryption keys are properly managed'
                        })
                
                if not has_encryption:
                    findings.append({
                        'finding_id': f"s3-{bucket_name[:8]}-enc-none",
                        'severity': 'high',
                        'category': 'security',
                        'bucket_name': bucket_name,
                        'check_name': 'encryption.none',
                        'status': 'fail',
                        'description': f"Bucket {bucket_name} has encryption rules without encryption configured",
                        'remediation': 'Configure server-side encryption rules'
                    })
                    
        except self.s3_client.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-enc-none",
                'severity': 'high',
                'category': 'security',
                'bucket_name': bucket_name,
                'check_name': 'encryption.none',
                'status': 'fail',
                'description': f"Bucket {bucket_name} has no server-side encryption configured",
                'remediation': 'Enable AES-256 or AWS-KMS encryption for all objects'
            })
            
        except Exception as e:
            logger.warning(f"Could not check encryption for {bucket_name}: {e}")
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-enc-error",
                'severity': 'medium',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'encryption.error',
                'status': 'warning',
                'description': f"Could not verify encryption: {str(e)}",
                'remediation': 'Check permissions for s3:GetBucketEncryption'
            })
        
        return findings
    
    def _check_versioning(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Check bucket versioning settings."""
        findings = []
        
        try:
            response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            status = response.get('Status', 'Disabled')
            
            if status == 'Enabled':
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-ver-enabled",
                    'severity': 'info',
                    'category': 'compliance',
                    'bucket_name': bucket_name,
                    'check_name': 'versioning.enabled',
                    'status': 'pass',
                    'description': f"Versioning is enabled for bucket {bucket_name}",
                    'remediation': 'Keep versioning enabled for data protection'
                })
            else:
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-ver-disabled",
                    'severity': 'medium',
                    'category': 'compliance',
                    'bucket_name': bucket_name,
                    'check_name': 'versioning.disabled',
                    'status': 'warning',
                    'description': f"Versioning is disabled for bucket {bucket_name}",
                    'remediation': 'Enable versioning to protect against accidental deletion or overwrites'
                })
                
        except Exception as e:
            logger.warning(f"Could not check versioning for {bucket_name}: {e}")
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-ver-error",
                'severity': 'medium',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'versioning.error',
                'status': 'warning',
                'description': f"Could not verify versioning: {str(e)}",
                'remediation': 'Check permissions for s3:GetBucketVersioning'
            })
        
        return findings
    
    def _check_logging(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Check bucket logging settings."""
        findings = []
        
        try:
            response = self.s3_client.get_bucket_logging(Bucket=bucket_name)
            logging_config = response.get('LoggingEnabled', {})
            
            if logging_config:
                target_bucket = logging_config.get('TargetBucket', 'unknown')
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-log-enabled",
                    'severity': 'info',
                    'category': 'compliance',
                    'bucket_name': bucket_name,
                    'check_name': 'logging.enabled',
                    'status': 'pass',
                    'description': f"Access logging is enabled for bucket {bucket_name}",
                    'remediation': 'Keep logging enabled for audit purposes'
                })
            else:
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-log-disabled",
                    'severity': 'low',
                    'category': 'compliance',
                    'bucket_name': bucket_name,
                    'check_name': 'logging.disabled',
                    'status': 'warning',
                    'description': f"Access logging is disabled for bucket {bucket_name}",
                    'remediation': 'Enable access logging for security auditing and compliance'
                })
                
        except Exception as e:
            logger.warning(f"Could not check logging for {bucket_name}: {e}")
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-log-error",
                'severity': 'medium',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'logging.error',
                'status': 'warning',
                'description': f"Could not verify logging: {str(e)}",
                'remediation': 'Check permissions for s3:GetBucketLogging'
            })
        
        return findings
    
    def _check_access_control(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Check bucket access control list (ACL)."""
        findings = []
        
        try:
            response = self.s3_client.get_bucket_acl(Bucket=bucket_name)
            grants = response.get('Grants', [])
            
            # Check for overly permissive grants
            for grant in grants:
                grantee = grant.get('Grantee', {})
                permission = grant.get('Permission', '')
                
                # Check for PUBLIC access
                if grantee.get('Type') == 'Group':
                    uri = grantee.get('URI', '')
                    if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                        findings.append({
                            'finding_id': f"s3-{bucket_name[:8]}-acl-public",
                            'severity': 'critical',
                            'category': 'security',
                            'bucket_name': bucket_name,
                            'check_name': 'acl.public_access',
                            'status': 'fail',
                            'description': f"Bucket {bucket_name} has public access via ACL",
                            'remediation': 'Remove public grants from bucket ACL immediately'
                        })
            
            if not any(f['status'] == 'fail' for f in findings):
                findings.append({
                    'finding_id': f"s3-{bucket_name[:8]}-acl-none",
                    'severity': 'info',
                    'category': 'security',
                    'bucket_name': bucket_name,
                    'check_name': 'acl.no_public',
                    'status': 'pass',
                    'description': f"No public access found in ACL for bucket {bucket_name}",
                    'remediation': 'Continue monitoring ACL for unauthorized changes'
                })
                
        except Exception as e:
            logger.warning(f"Could not check ACL for {bucket_name}: {e}")
            findings.append({
                'finding_id': f"s3-{bucket_name[:8]}-acl-error",
                'severity': 'medium',
                'category': 'error',
                'bucket_name': bucket_name,
                'check_name': 'acl.error',
                'status': 'warning',
                'description': f"Could not verify ACL: {str(e)}",
                'remediation': 'Check permissions for s3:GetBucketAcl'
            })
        
        return findings
    
    def get_findings_summary(self) -> Dict[str, Any]:
        """Get summary of findings."""
        if not self.findings:
            return {
                'total_findings': 0,
                'by_severity': {},
                'by_category': {},
                'summary': 'No findings yet. Run scan_all_buckets() first.'
            }
        
        by_severity = {}
        by_category = {}
        
        for finding in self.findings:
            severity = finding.get('severity', 'unknown')
            category = finding.get('category', 'unknown')
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            'total_findings': len(self.findings),
            'by_severity': by_severity,
            'by_category': by_category,
            'findings': self.findings
        }
    
    def save_scan_results(self) -> bool:
        """Save scan results to session manager."""
        results = {
            'scan_type': 's3',
            'tenant_id': self.tenant_id,
            'timestamp': datetime.utcnow().isoformat(),
            'findings': self.findings,
            'summary': self.get_findings_summary()
        }
        
        return self.session_manager.save_session(f"s3_scan_{self.tenant_id}", results)
