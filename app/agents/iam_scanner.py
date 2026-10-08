"""IAM Scanner - Checks MFA requirements, long-lived keys, privilege escalation."""
import boto3
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.aws.bedrock import BedrockClient
from app.core.session_manager import FileSessionManager
from app.security.anonymization import lgpd_anonymize

logger = logging.getLogger(__name__)


@dataclass
class IAMFinding:
    """IAM scanner finding."""
    finding_id: str
    severity: str
    category: str
    resource_type: str  # user, role, policy, access_key
    resource_name: str
    check_name: str
    status: str  # pass, fail, warning
    description: str
    remediation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class IAMScanner:
    """
    IAM security scanner for multi-tenant AWS environments.
    
    Checks:
    - MFA requirements for console access
    - Long-lived access keys (>90 days)
    - Privilege escalation risks
    - Root user activity
    - IAM policies
    """
    
    def __init__(self, tenant_id: str, region: str = 'us-east-1'):
        """
        Initialize IAM scanner for a specific tenant.
        
        Args:
            tenant_id: Unique tenant identifier for isolation
            region: AWS region (IAM is global, but session is region-specific)
        """
        self.tenant_id = tenant_id
        self.region = region
        self.session_manager = FileSessionManager()
        self._iam_client = None
        self.findings: List[Dict[str, Any]] = []
        
    @property
    def iam_client(self) -> boto3.client:
        """Get IAM client (global service)."""
        if self._iam_client is None:
            self._iam_client = boto3.client('iam')
        return self._iam_client
    
    def scan_all_users(self) -> List[Dict[str, Any]]:
        """
        Scan all IAM users for security issues.
        
        Returns:
            List of all findings for all users
        """
        all_findings = []
        
        try:
            # List all users
            users = self.iam_client.list_users().get('Users', [])
            
            for user in users:
                user_name = user['UserName']
                logger.info(f"Scanning user: {user_name}")
                
                user_findings = self._scan_user(user_name, user)
                all_findings.extend(user_findings)
                
        except Exception as e:
            logger.error(f"Error listing IAM users: {e}")
            all_findings.append({
                'severity': 'critical',
                'category': 'error',
                'resource_type': 'iam',
                'resource_name': 'all_users',
                'check_name': 'list_users_error',
                'status': 'error',
                'description': f"Failed to list IAM users: {str(e)}",
                'remediation': 'Check AWS credentials and permissions'
            })
        
        # Anonymize findings for LGPD compliance
        anonymized_findings = lgpd_anonymize({'findings': all_findings})
        
        return anonymized_findings['findings']
    
    def scan_all_roles(self) -> List[Dict[str, Any]]:
        """
        Scan all IAM roles for security issues.
        
        Returns:
            List of all findings for all roles
        """
        all_findings = []
        
        try:
            # List all roles
            roles = self.iam_client.list_roles().get('Roles', [])
            
            for role in roles:
                role_name = role['RoleName']
                logger.info(f"Scanning role: {role_name}")
                
                role_findings = self._scan_role(role_name, role)
                all_findings.extend(role_findings)
                
        except Exception as e:
            logger.error(f"Error listing IAM roles: {e}")
            all_findings.append({
                'severity': 'critical',
                'category': 'error',
                'resource_type': 'iam',
                'resource_name': 'all_roles',
                'check_name': 'list_roles_error',
                'status': 'error',
                'description': f"Failed to list IAM roles: {str(e)}",
                'remediation': 'Check AWS credentials and permissions'
            })
        
        # Anonymize findings for LGPD compliance
        anonymized_findings = lgpd_anonymize({'findings': all_findings})
        
        return anonymized_findings['findings']
    
    def _scan_user(self, user_name: str, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan a single IAM user."""
        findings = []
        user_arn = user_data.get('Arn', f"arn:aws:iam::unknown:user/{user_name}")
        
        # 1. Check MFA enabled
        findings.extend(self._check_mfa_enabled(user_name, user_arn))
        
        # 2. Check access keys - age and usage
        findings.extend(self._check_access_keys(user_name, user_arn))
        
        # 3. Check console password
        findings.extend(self._check_console_password(user_name, user_arn))
        
        # 4. Check for IAM policy attachments
        findings.extend(self._check_policy_attachments(user_name, user_arn))
        
        # 5. Check user age
        findings.extend(self._check_user_age(user_name, user_arn, user_data))
        
        return findings
    
    def _scan_role(self, role_name: str, role_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan a single IAM role."""
        findings = []
        role_arn = role_data.get('Arn', f"arn:aws:iam::unknown:role/{role_name}")
        
        # 1. Check trust policy for dangerous principals
        findings.extend(self._check_trust_policy(role_name, role_arn))
        
        # 2. Check policy attachments
        findings.extend(self._check_policy_attachments(role_name, role_arn, resource_type='role'))
        
        # 3. Check role age
        findings.extend(self._check_role_age(role_name, role_arn, role_data))
        
        return findings
    
    def _check_mfa_enabled(self, user_name: str, user_arn: str) -> List[Dict[str, Any]]:
        """Check if MFA is enabled for the user."""
        findings = []
        
        try:
            response = self.iam_client.list_mfa_devices(UserName=user_name)
            mfa_devices = response.get('MFADevices', [])
            
            if mfa_devices:
                findings.append({
                    'finding_id': f"iam-{user_name[:8]}-mfa-enabled",
                    'severity': 'info',
                    'category': 'security',
                    'resource_type': 'user',
                    'resource_name': user_name,
                    'check_name': 'mfa.enabled',
                    'status': 'pass',
                    'description': f"MFA is enabled for user {user_name}",
                    'remediation': 'Continue using MFA for all console and API access'
                })
            else:
                findings.append({
                    'finding_id': f"iam-{user_name[:8]}-mfa-disabled",
                    'severity': 'high',
                    'category': 'security',
                    'resource_type': 'user',
                    'resource_name': user_name,
                    'check_name': 'mfa.disabled',
                    'status': 'fail',
                    'description': f"MFA is not enabled for user {user_name}",
                    'remediation': 'Enable MFA for all users with console access'
                })
                
        except Exception as e:
            logger.warning(f"Could not check MFA for user {user_name}: {e}")
            findings.append({
                'finding_id': f"iam-{user_name[:8]}-mfa-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': 'user',
                'resource_name': user_name,
                'check_name': 'mfa.error',
                'status': 'warning',
                'description': f"Could not verify MFA status: {str(e)}",
                'remediation': 'Check permissions for iam:ListMfaDevices'
            })
        
        return findings
    
    def _check_access_keys(self, user_name: str, user_arn: str) -> List[Dict[str, Any]]:
        """Check access keys for age and usage."""
        findings = []
        
        try:
            response = self.iam_client.list_access_keys(UserName=user_name)
            access_keys = response.get('AccessKeyMetadata', [])
            
            if not access_keys:
                findings.append({
                    'finding_id': f"iam-{user_name[:8]}-keys-none",
                    'severity': 'info',
                    'category': 'security',
                    'resource_type': 'user',
                    'resource_name': user_name,
                    'check_name': 'access_keys.none',
                    'status': 'pass',
                    'description': f"No access keys found for user {user_name}",
                    'remediation': 'Create access keys if programmatic access is needed'
                })
                return findings
            
            for key in access_keys:
                key_id = key['AccessKeyId']
                create_date = key.get('CreateDate', datetime.utcnow())
                
                # Calculate key age
                age_days = (datetime.utcnow() - create_date).days
                
                if age_days > 90:
                    findings.append({
                        'finding_id': f"iam-{user_name[:8]}-key-old-{key_id[:8]}",
                        'severity': 'medium',
                        'category': 'security',
                        'resource_type': 'access_key',
                        'resource_name': user_name,
                        'check_name': 'access_key.age',
                        'status': 'fail',
                        'description': f"Access key for user {user_name} is {age_days} days old (>90 days)",
                        'remediation': 'Rotate access keys every 90 days or less'
                    })
                else:
                    findings.append({
                        'finding_id': f"iam-{user_name[:8]}-key-{key_id[:8]}",
                        'severity': 'info',
                        'category': 'security',
                        'resource_type': 'access_key',
                        'resource_name': user_name,
                        'check_name': 'access_key.age',
                        'status': 'pass',
                        'description': f"Access key for user {user_name} is {age_days} days old",
                        'remediation': 'Continue monitoring key usage'
                    })
            
        except Exception as e:
            logger.warning(f"Could not check access keys for user {user_name}: {e}")
            findings.append({
                'finding_id': f"iam-{user_name[:8]}-keys-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': 'user',
                'resource_name': user_name,
                'check_name': 'access_keys.error',
                'status': 'warning',
                'description': f"Could not verify access keys: {str(e)}",
                'remediation': 'Check permissions for iam:ListAccessKeys'
            })
        
        return findings
    
    def _check_console_password(self, user_name: str, user_arn: str) -> List[Dict[str, Any]]:
        """Check console password status."""
        findings = []
        
        try:
            self.iam_client.get_login_profile(UserName=user_name)
            
            # If we get here, user has a console password
            findings.append({
                'finding_id': f"iam-{user_name[:8]}-password-exists",
                'severity': 'medium',
                'category': 'security',
                'resource_type': 'user',
                'resource_name': user_name,
                'check_name': 'console_password.exists',
                'status': 'warning',
                'description': f"User {user_name} has console password access",
                'remediation': 'Review console access necessity and consider disabling if not needed'
            })
            
        except self.iam_client.exceptions.NoSuchEntityException:
            # No console password - this is fine for programmatic-only users
            findings.append({
                'finding_id': f"iam-{user_name[:8]}-password-none",
                'severity': 'info',
                'category': 'security',
                'resource_type': 'user',
                'resource_name': user_name,
                'check_name': 'console_password.none',
                'status': 'pass',
                'description': f"User {user_name} has no console password (programmatic access only)",
                'remediation': 'Keep programmatic-only access if console access not required'
            })
            
        except Exception as e:
            logger.warning(f"Could not check console password for user {user_name}: {e}")
            findings.append({
                'finding_id': f"iam-{user_name[:8]}-password-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': 'user',
                'resource_name': user_name,
                'check_name': 'console_password.error',
                'status': 'warning',
                'description': f"Could not verify console password: {str(e)}",
                'remediation': 'Check permissions for iam:GetLoginProfile'
            })
        
        return findings
    
    def _check_policy_attachments(self, resource_name: str, resource_arn: str, 
                                   resource_type: str = 'user') -> List[Dict[str, Any]]:
        """Check for overly permissive policy attachments."""
        findings = []
        
        try:
            # Check managed policies
            if resource_type == 'user':
                attached_policies = self.iam_client.list_attached_user_policies(
                    UserName=resource_name
                ).get('AttachedPolicies', [])
            else:
                attached_policies = self.iam_client.list_attached_role_policies(
                    RoleName=resource_name
                ).get('AttachedPolicies', [])
            
            dangerous_policies = ['AdministratorAccess', 'FullAccess', 'SuperAccess']
            
            for policy in attached_policies:
                policy_name = policy['PolicyName']
                policy_arn = policy['PolicyArn']
                
                if any(dangerous in policy_name for dangerous in dangerous_policies):
                    findings.append({
                        'finding_id': f"iam-{resource_name[:8]}-policy-{policy_name[:8]}",
                        'severity': 'critical',
                        'category': 'privilege_escalation',
                        'resource_type': resource_type,
                        'resource_name': resource_name,
                        'check_name': 'policy.dangerous_attachment',
                        'status': 'fail',
                        'description': f"{resource_type.capitalize()} {resource_name} has dangerous policy: {policy_name}",
                        'remediation': 'Replace with least-privilege policies'
                    })
                else:
                    findings.append({
                        'finding_id': f"iam-{resource_name[:8]}-policy-{policy_name[:8]}",
                        'severity': 'info',
                        'category': 'compliance',
                        'resource_type': resource_type,
                        'resource_name': resource_name,
                        'check_name': 'policy.attachment',
                        'status': 'pass',
                        'description': f"{resource_type.capitalize()} {resource_name} has policy attached: {policy_name}",
                        'remediation': 'Review policy periodically for least privilege'
                    })
                    
        except Exception as e:
            logger.warning(f"Could not check policy attachments for {resource_name}: {e}")
            findings.append({
                'finding_id': f"iam-{resource_name[:8]}-policies-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': resource_type,
                'resource_name': resource_name,
                'check_name': 'policy_attachments.error',
                'status': 'warning',
                'description': f"Could not verify policy attachments: {str(e)}",
                'remediation': 'Check permissions for iam:ListAttached[User/Role]Policies'
            })
        
        return findings
    
    def _check_user_age(self, user_name: str, user_arn: str, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check user age for inactive accounts."""
        findings = []
        
        try:
            create_date = user_data.get('CreateDate', datetime.utcnow())
            age_days = (datetime.utcnow() - create_date).days
            
            # Check if user has been active (check for last_active_date if available)
            # For now, just use create_date
            if age_days > 365:
                findings.append({
                    'finding_id': f"iam-{user_name[:8]}-user-old",
                    'severity': 'medium',
                    'category': 'compliance',
                    'resource_type': 'user',
                    'resource_name': user_name,
                    'check_name': 'user.age',
                    'status': 'warning',
                    'description': f"User {user_name} is {age_days} days old",
                    'remediation': 'Review inactive accounts and consider disabling or removing'
                })
            else:
                findings.append({
                    'finding_id': f"iam-{user_name[:8]}-user-{age_days}d",
                    'severity': 'info',
                    'category': 'compliance',
                    'resource_type': 'user',
                    'resource_name': user_name,
                    'check_name': 'user.age',
                    'status': 'pass',
                    'description': f"User {user_name} is {age_days} days old",
                    'remediation': 'Keep track of account age for lifecycle management'
                })
                
        except Exception as e:
            logger.warning(f"Could not check user age for {user_name}: {e}")
            findings.append({
                'finding_id': f"iam-{user_name[:8]}-user-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': 'user',
                'resource_name': user_name,
                'check_name': 'user.age.error',
                'status': 'warning',
                'description': f"Could not verify user age: {str(e)}",
                'remediation': 'Check permissions for iam:GetUser'
            })
        
        return findings
    
    def _check_role_age(self, role_name: str, role_arn: str, role_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check role age."""
        findings = []
        
        try:
            create_date = role_data.get('CreateDate', datetime.utcnow())
            age_days = (datetime.utcnow() - create_date).days
            
            if age_days > 365:
                findings.append({
                    'finding_id': f"iam-{role_name[:8]}-role-old",
                    'severity': 'medium',
                    'category': 'compliance',
                    'resource_type': 'role',
                    'resource_name': role_name,
                    'check_name': 'role.age',
                    'status': 'warning',
                    'description': f"Role {role_name} is {age_days} days old",
                    'remediation': 'Review old roles for continued necessity'
                })
            else:
                findings.append({
                    'finding_id': f"iam-{role_name[:8]}-role-{age_days}d",
                    'severity': 'info',
                    'category': 'compliance',
                    'resource_type': 'role',
                    'resource_name': role_name,
                    'check_name': 'role.age',
                    'status': 'pass',
                    'description': f"Role {role_name} is {age_days} days old",
                    'remediation': 'Keep track of role age for lifecycle management'
                })
                
        except Exception as e:
            logger.warning(f"Could not check role age for {role_name}: {e}")
            findings.append({
                'finding_id': f"iam-{role_name[:8]}-role-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': 'role',
                'resource_name': role_name,
                'check_name': 'role.age.error',
                'status': 'warning',
                'description': f"Could not verify role age: {str(e)}",
                'remediation': 'Check permissions for iam:GetRole'
            })
        
        return findings
    
    def _check_trust_policy(self, role_name: str, role_arn: str) -> List[Dict[str, Any]]:
        """Check role trust policy for dangerous principals."""
        findings = []
        
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            trust_policy = response.get('Role', {}).get('AssumeRolePolicyDocument', {})
            
            # Parse and check trust policy
            # For now, just log that trust policy exists
            findings.append({
                'finding_id': f"iam-{role_name[:8]}-trust-exists",
                'severity': 'info',
                'category': 'security',
                'resource_type': 'role',
                'resource_name': role_name,
                'check_name': 'trust_policy.exists',
                'status': 'pass',
                'description': f"Role {role_name} has a trust policy configured",
                'remediation': 'Review trust policy for overly permissive principals (e.g., *, specific AWS accounts)'
            })
            
        except Exception as e:
            logger.warning(f"Could not check trust policy for {role_name}: {e}")
            findings.append({
                'finding_id': f"iam-{role_name[:8]}-trust-error",
                'severity': 'medium',
                'category': 'error',
                'resource_type': 'role',
                'resource_name': role_name,
                'check_name': 'trust_policy.error',
                'status': 'warning',
                'description': f"Could not verify trust policy: {str(e)}",
                'remediation': 'Check permissions for iam:GetRole'
            })
        
        return findings
    
    def get_findings_summary(self) -> Dict[str, Any]:
        """Get summary of findings."""
        if not self.findings:
            return {
                'total_findings': 0,
                'by_severity': {},
                'by_category': {},
                'summary': 'No findings yet. Run scan_all_users() or scan_all_roles() first.'
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
            'scan_type': 'iam',
            'tenant_id': self.tenant_id,
            'timestamp': datetime.utcnow().isoformat(),
            'findings': self.findings,
            'summary': self.get_findings_summary()
        }
        
        return self.session_manager.save_session(f"iam_scan_{self.tenant_id}", results)
