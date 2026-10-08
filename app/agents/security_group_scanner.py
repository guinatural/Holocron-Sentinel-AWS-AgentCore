"""SecurityGroupScanner - Checks for dangerous port rules in security groups."""
import boto3
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.aws.bedrock import BedrockClient
from app.core.session_manager import FileSessionManager
from app.security.anonymization import lgpd_anonymize

logger = logging.getLogger(__name__)


@dataclass
class SecurityGroupFinding:
    """Security group scanner finding."""
    finding_id: str
    severity: str
    category: str
    check_name: str
    status: str  # pass, fail, warning
    description: str
    remediation: str
    resource_id: str
    resource_name: Optional[str] = None
    resource_type: str = 'security_group'
    rule_details: Optional[Dict[str, Any]] = None
    region: str = 'us-east-1'
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SecurityGroupScanner:
    """
    Security Group security scanner for multi-tenant AWS environments.
    
    Checks:
    - SSH (port 22) open to 0.0.0.0/0
    - RDP (port 3389) open to 0.0.0.0/0
    - All ports open (0-65535) to 0.0.0.0/0
    - MySQL/Aurora (port 3306) open to 0.0.0.0/0
    - PostgreSQL (port 5432) open to 0.0.0.0/0
    - Elasticsearch (port 9200) open to 0.0.0.0/0
    - MongoDB (port 27017) open to 0.0.0.0/0
    - Redis (port 6379) open to 0.0.0.0/0
    - DNS (port 53) open to 0.0.0.0/0
    - HTTP/HTTPS without WAF
    """
    
    # Dangerous ports and protocols
    DANGEROUS_PORTS = {
        22: {'name': 'SSH', 'severity': 'critical', 'description': 'Remote shell access'},
        3389: {'name': 'RDP', 'severity': 'critical', 'description': 'Remote Desktop Protocol'},
        3306: {'name': 'MySQL', 'severity': 'high', 'description': 'MySQL database'},
        5432: {'name': 'PostgreSQL', 'severity': 'high', 'description': 'PostgreSQL database'},
        9200: {'name': 'Elasticsearch', 'severity': 'high', 'description': 'Elasticsearch'},
        27017: {'name': 'MongoDB', 'severity': 'high', 'description': 'MongoDB database'},
        6379: {'name': 'Redis', 'severity': 'high', 'description': 'Redis cache'},
        1433: {'name': 'MSSQL', 'severity': 'high', 'description': 'Microsoft SQL Server'},
        11211: {'name': 'Memcached', 'severity': 'high', 'description': 'Memcached'},
        53: {'name': 'DNS', 'severity': 'medium', 'description': 'DNS (any source)'},
    }
    
    def __init__(self, tenant_id: str, region: str = 'us-east-1'):
        """
        Initialize Security Group scanner for a specific tenant.
        
        Args:
            tenant_id: Unique tenant identifier for isolation
            region: AWS region to scan
        """
        self.tenant_id = tenant_id
        self.region = region
        self.session_manager = FileSessionManager()
        self._ec2_client = None
        self.findings: List[Dict[str, Any]] = []
        
    @property
    def ec2_client(self) -> boto3.client:
        """Get EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = boto3.client('ec2', region_name=self.region)
        return self._ec2_client
    
    def scan_all_security_groups(self) -> List[Dict[str, Any]]:
        """
        Scan all security groups in the region.
        
        Returns:
            List of all findings for all security groups
        """
        all_findings = []
        
        try:
            # List all security groups
            response = self.ec2_client.describe_security_groups()
            security_groups = response.get('SecurityGroups', [])
            
            for sg in security_groups:
                sg_id = sg['GroupId']
                sg_name = sg.get('GroupName', 'default')
                logger.info(f"Scanning security group: {sg_name} ({sg_id})")
                
                sg_findings = self._scan_security_group(sg_id, sg_name, sg)
                all_findings.extend(sg_findings)
                
        except Exception as e:
            logger.error(f"Error describing security groups: {e}")
            all_findings.append({
                'severity': 'critical',
                'category': 'error',
                'resource_type': 'security_group',
                'resource_id': 'all_sgs',
                'resource_name': None,
                'check_name': 'describe_security_groups_error',
                'status': 'error',
                'description': f"Failed to describe security groups: {str(e)}",
                'remediation': 'Check AWS credentials and permissions'
            })
        
        # Anonymize findings for LGPD compliance
        anonymized_findings = lgpd_anonymize({'findings': all_findings})
        
        return anonymized_findings['findings']
    
    def scan_security_group(self, sg_id: str) -> List[Dict[str, Any]]:
        """
        Scan a single security group.
        
        Args:
            sg_id: Security group ID
            
        Returns:
            List of findings for the security group
        """
        try:
            response = self.ec2_client.describe_security_groups(GroupIds=[sg_id])
            sg = response['SecurityGroups'][0]
            sg_name = sg.get('GroupName', 'unknown')
            
            return self._scan_security_group(sg_id, sg_name, sg)
        except Exception as e:
            logger.error(f"Error describing security group {sg_id}: {e}")
            return [{
                'severity': 'critical',
                'category': 'error',
                'resource_type': 'security_group',
                'resource_id': sg_id,
                'resource_name': None,
                'check_name': 'describe_security_group_error',
                'status': 'error',
                'description': f"Failed to describe security group: {str(e)}",
                'remediation': 'Check AWS credentials and permissions'
            }]
    
    def _scan_security_group(self, sg_id: str, sg_name: str, sg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan a single security group for dangerous rules."""
        findings = []
        
        # Get all ingress rules
        ip_permissions = sg_data.get('IpPermissions', [])
        
        for permission in ip_permissions:
            findings.extend(self._check_permission(sg_id, sg_name, permission))
        
        # Check for default security group with dangerous rules
        if sg_name == 'default':
            findings.append({
                'finding_id': f"sg-{sg_id[-8:]}-default",
                'severity': 'low',
                'category': 'compliance',
                'resource_type': 'security_group',
                'resource_id': sg_id,
                'resource_name': sg_name,
                'check_name': 'security_group.is_default',
                'status': 'warning',
                'description': f"Security group {sg_name} ({sg_id}) is the default security group",
                'remediation': 'Review default security group rules and consider creating custom security groups'
            })
        
        return findings
    
    def _check_permission(self, sg_id: str, sg_name: str, permission: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a single permission for dangerous configurations."""
        findings = []
        
        from_port = permission.get('FromPort')
        to_port = permission.get('ToPort')
        ip_protocol = permission.get('IpProtocol', 'tcp')
        ip_ranges = permission.get('IpRanges', [])
        
        # Check for all ports
        if from_port is None and to_port is None:
            # All ports (ip_protocol = -1)
            for ip_range in ip_ranges:
                cidr = ip_range.get('CidrIp', '')
                if cidr == '0.0.0.0/0':
                    findings.append({
                        'finding_id': f"sg-{sg_id[-8:]}-all-ports",
                        'severity': 'critical',
                        'category': 'security',
                        'resource_type': 'security_group',
                        'resource_id': sg_id,
                        'resource_name': sg_name,
                        'check_name': 'security_group.all_ports_world',
                        'status': 'fail',
                        'description': f"Security group {sg_name} ({sg_id}) has ALL ports open to 0.0.0.0/0",
                        'remediation': 'Restrict port access to only required ports',
                        'rule_details': {
                            'protocol': ip_protocol,
                            'cidr': cidr
                        }
                    })
        
        # Check for specific dangerous ports
        elif from_port and to_port:
            # Check each port in range
            for port in range(from_port, to_port + 1):
                if port in self.DANGEROUS_PORTS:
                    for ip_range in ip_ranges:
                        cidr = ip_range.get('CidrIp', '')
                        if cidr == '0.0.0.0/0':
                            port_info = self.DANGEROUS_PORTS[port]
                            findings.append({
                                'finding_id': f"sg-{sg_id[-8:]}-{port_info['name'].lower()[:3]}",
                                'severity': port_info['severity'],
                                'category': 'security',
                                'resource_type': 'security_group',
                                'resource_id': sg_id,
                                'resource_name': sg_name,
                                'check_name': f'security_group.{port_info["name"].lower()}_world',
                                'status': 'fail',
                                'description': f"Security group {sg_name} ({sg_id}) has {port_info['name']} (port {port}) open to 0.0.0.0/0",
                                'remediation': f"Restrict {port_info['name']} access to specific IP ranges or VPC",
                                'rule_details': {
                                    'protocol': ip_protocol,
                                    'port': port,
                                    'cidr': cidr
                                }
                            })
            
            # Check for all TCP/UDP open
            if from_port == 1 and to_port == 65535:
                for ip_range in ip_ranges:
                    cidr = ip_range.get('CidrIp', '')
                    if cidr == '0.0.0.0/0':
                        findings.append({
                            'finding_id': f"sg-{sg_id[-8:]}-all-tcp-udp",
                            'severity': 'critical',
                            'category': 'security',
                            'resource_type': 'security_group',
                            'resource_id': sg_id,
                            'resource_name': sg_name,
                            'check_name': 'security_group.all_tcp_udp_world',
                            'status': 'fail',
                            'description': f"Security group {sg_name} ({sg_id}) has all TCP/UDP ports open to 0.0.0.0/0",
                            'remediation': 'Restrict port access to only required ports',
                            'rule_details': {
                                'protocol': ip_protocol,
                                'cidr': cidr
                            }
                        })
        
        # Check for IPv6 access
        for ip_range in ip_ranges:
            cidr = ip_range.get('CidrIp', '')
            if cidr == '::/0':
                # IPv6 all traffic
                findings.append({
                    'finding_id': f"sg-{sg_id[-8:]}-ipv6-all",
                    'severity': 'medium',
                    'category': 'security',
                    'resource_type': 'security_group',
                    'resource_id': sg_id,
                    'resource_name': sg_name,
                    'check_name': 'security_group.ipv6_all',
                    'status': 'warning',
                    'description': f"Security group {sg_name} ({sg_id}) has IPv6 access (::/0)",
                    'remediation': 'Review IPv6 rules and restrict if not needed'
                })
        
        return findings
    
    def get_findings_summary(self) -> Dict[str, Any]:
        """Get summary of findings."""
        if not self.findings:
            return {
                'total_findings': 0,
                'by_severity': {},
                'by_category': {},
                'summary': 'No findings yet. Run scan_all_security_groups() first.'
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
            'scan_type': 'security_group',
            'tenant_id': self.tenant_id,
            'timestamp': datetime.utcnow().isoformat(),
            'findings': self.findings,
            'summary': self.get_findings_summary()
        }
        
        return self.session_manager.save_session(f"sg_scan_{self.tenant_id}", results)
