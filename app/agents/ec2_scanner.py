"""EC2 Scanner - Checks EBS volumes in available state, SSH open to 0.0.0.0/0."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3

from app.core.session_manager import FileSessionManager
from app.security.anonymization import lgpd_anonymize

logger = logging.getLogger(__name__)


@dataclass
class EC2Finding:
    """EC2 scanner finding."""

    finding_id: str
    severity: str
    category: str
    resource_type: str  # instance, volume, security_group
    resource_id: str
    resource_name: Optional[str]
    check_name: str
    status: str  # pass, fail, warning
    description: str
    remediation: str
    region: str = "us-east-1"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EC2Scanner:
    """
    EC2 security scanner for multi-tenant AWS environments.

    Checks:
    - EBS volumes in available state (orphaned volumes)
    - SSH (port 22) open to 0.0.0.0/0
    - RDP (port 3389) open to 0.0.0.0/0
    - Instances without termination protection
    - Unencrypted EBS volumes
    """

    def __init__(self, tenant_id: str, region: str = "us-east-1"):
        """
        Initialize EC2 scanner for a specific tenant.

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
            self._ec2_client = boto3.client("ec2", region_name=self.region)
        return self._ec2_client

    def scan_all_instances(self) -> List[Dict[str, Any]]:
        """
        Scan all EC2 instances in the region.

        Returns:
            List of all findings for all instances
        """
        all_findings = []

        try:
            # List all instances
            response = self.ec2_client.describe_instances()
            reservations = response.get("Reservations", [])

            for reservation in reservations:
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]
                    logger.info(f"Scanning instance: {instance_id}")

                    instance_findings = self._scan_instance(instance_id, instance)
                    all_findings.extend(instance_findings)

        except Exception as e:
            logger.error(f"Error describing EC2 instances: {e}")
            all_findings.append(
                {
                    "severity": "critical",
                    "category": "error",
                    "resource_type": "ec2",
                    "resource_id": "all_instances",
                    "resource_name": None,
                    "check_name": "describe_instances_error",
                    "status": "error",
                    "description": f"Failed to describe EC2 instances: {str(e)}",
                    "remediation": "Check AWS credentials and permissions",
                }
            )

        # Anonymize findings for LGPD compliance
        anonymized_findings = lgpd_anonymize({"findings": all_findings})

        return anonymized_findings["findings"]

    def scan_all_volumes(self) -> List[Dict[str, Any]]:
        """
        Scan all EBS volumes in the region.

        Returns:
            List of all findings for all volumes
        """
        all_findings = []

        try:
            # List all volumes
            response = self.ec2_client.describe_volumes()
            volumes = response.get("Volumes", [])

            for volume in volumes:
                volume_id = volume["VolumeId"]
                logger.info(f"Scanning volume: {volume_id}")

                volume_findings = self._scan_volume(volume_id, volume)
                all_findings.extend(volume_findings)

        except Exception as e:
            logger.error(f"Error describing EBS volumes: {e}")
            all_findings.append(
                {
                    "severity": "critical",
                    "category": "error",
                    "resource_type": "ec2",
                    "resource_id": "all_volumes",
                    "resource_name": None,
                    "check_name": "describe_volumes_error",
                    "status": "error",
                    "description": f"Failed to describe EBS volumes: {str(e)}",
                    "remediation": "Check AWS credentials and permissions",
                }
            )

        # Anonymize findings for LGPD compliance
        anonymized_findings = lgpd_anonymize({"findings": all_findings})

        return anonymized_findings["findings"]

    def _scan_instance(
        self, instance_id: str, instance_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Scan a single EC2 instance."""
        findings = []
        state = instance_data.get("State", {}).get("Name", "unknown")
        instance_name = self._get_instance_name(instance_data)

        # 1. Check SSH open to world
        findings.extend(self._check_ssh_open_to_world(instance_id, instance_name))

        # 2. Check RDP open to world
        findings.extend(self._check_rdp_open_to_world(instance_id, instance_name))

        # 3. Check termination protection
        findings.extend(
            self._check_termination_protection(
                instance_id, instance_name, instance_data
            )
        )

        # 4. Check instance state
        findings.extend(self._check_instance_state(instance_id, instance_name, state))

        # 5. Check EBS encryption for root volume
        findings.extend(self._check_root_volume_encryption(instance_id, instance_name))

        return findings

    def _scan_volume(
        self, volume_id: str, volume_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Scan a single EBS volume."""
        findings = []
        volume_state = volume_data.get("State", "unknown")
        volume_name = self._get_volume_name(volume_data)

        # 1. Check for orphaned volumes (available state, not attached)
        findings.extend(
            self._check_orphaned_volume(
                volume_id, volume_name, volume_state, volume_data
            )
        )

        # 2. Check encryption
        findings.extend(
            self._check_volume_encryption(volume_id, volume_name, volume_data)
        )

        # 3. Check volume age
        findings.extend(self._check_volume_age(volume_id, volume_name, volume_data))

        return findings

    def _check_ssh_open_to_world(
        self, instance_id: str, instance_name: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Check if SSH (port 22) is open to 0.0.0.0/0."""
        findings = []

        try:
            # Get security groups for this instance
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            security_groups = instance.get("SecurityGroups", [])

            for sg in security_groups:
                sg_id = sg["GroupId"]
                sg_rules = self._get_security_group_rules(sg_id)

                # Check for SSH rules
                for rule in sg_rules:
                    if rule.get("FromPort") == 22 and rule.get("ToPort") == 22:
                        for ip_range in rule.get("IpRanges", []):
                            if ip_range.get("CidrIp") == "0.0.0.0/0":
                                findings.append(
                                    {
                                        "finding_id": f"ec2-{instance_id[-8:]}-ssh-world",
                                        "severity": "critical",
                                        "category": "security",
                                        "resource_type": "instance",
                                        "resource_id": instance_id,
                                        "resource_name": instance_name,
                                        "check_name": "security_group.ssh_world",
                                        "status": "fail",
                                        "description": f"Instance {instance_id} has SSH (port 22) open to 0.0.0.0/0 via security group {sg_id}",
                                        "remediation": "Restrict SSH access to specific IP ranges or use VPN",
                                    }
                                )

        except Exception as e:
            logger.warning(f"Could not check SSH for instance {instance_id}: {e}")
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-ssh-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "security_group.ssh_error",
                    "status": "warning",
                    "description": f"Could not verify SSH configuration: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeInstances and ec2:DescribeSecurityGroups",
                }
            )

        return findings

    def _check_rdp_open_to_world(
        self, instance_id: str, instance_name: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Check if RDP (port 3389) is open to 0.0.0.0/0."""
        findings = []

        try:
            # Get security groups for this instance
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            security_groups = instance.get("SecurityGroups", [])

            for sg in security_groups:
                sg_id = sg["GroupId"]
                sg_rules = self._get_security_group_rules(sg_id)

                # Check for RDP rules
                for rule in sg_rules:
                    if rule.get("FromPort") == 3389 and rule.get("ToPort") == 3389:
                        for ip_range in rule.get("IpRanges", []):
                            if ip_range.get("CidrIp") == "0.0.0.0/0":
                                findings.append(
                                    {
                                        "finding_id": f"ec2-{instance_id[-8:]}-rdp-world",
                                        "severity": "critical",
                                        "category": "security",
                                        "resource_type": "instance",
                                        "resource_id": instance_id,
                                        "resource_name": instance_name,
                                        "check_name": "security_group.rdp_world",
                                        "status": "fail",
                                        "description": f"Instance {instance_id} has RDP (port 3389) open to 0.0.0.0/0 via security group {sg_id}",
                                        "remediation": "Restrict RDP access to specific IP ranges or use VPN",
                                    }
                                )

        except Exception as e:
            logger.warning(f"Could not check RDP for instance {instance_id}: {e}")
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-rdp-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "security_group.rdp_error",
                    "status": "warning",
                    "description": f"Could not verify RDP configuration: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeInstances and ec2:DescribeSecurityGroups",
                }
            )

        return findings

    def _check_termination_protection(
        self,
        instance_id: str,
        instance_name: Optional[str],
        instance_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check if termination protection is enabled."""
        findings = []

        try:
            termination_protection = instance_data.get("DisableApiTermination", False)

            if termination_protection:
                findings.append(
                    {
                        "finding_id": f"ec2-{instance_id[-8:]}-term-protected",
                        "severity": "info",
                        "category": "security",
                        "resource_type": "instance",
                        "resource_id": instance_id,
                        "resource_name": instance_name,
                        "check_name": "termination_protection.enabled",
                        "status": "pass",
                        "description": f"Termination protection is enabled for instance {instance_id}",
                        "remediation": "Keep termination protection enabled for critical instances",
                    }
                )
            else:
                findings.append(
                    {
                        "finding_id": f"ec2-{instance_id[-8:]}-term unprotected",
                        "severity": "medium",
                        "category": "security",
                        "resource_type": "instance",
                        "resource_id": instance_id,
                        "resource_name": instance_name,
                        "check_name": "termination_protection.disabled",
                        "status": "warning",
                        "description": f"Termination protection is NOT enabled for instance {instance_id}",
                        "remediation": "Enable termination protection for critical instances",
                    }
                )

        except Exception as e:
            logger.warning(
                f"Could not check termination protection for {instance_id}: {e}"
            )
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-term-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "termination_protection.error",
                    "status": "warning",
                    "description": f"Could not verify termination protection: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeInstances",
                }
            )

        return findings

    def _check_instance_state(
        self, instance_id: str, instance_name: Optional[str], state: str
    ) -> List[Dict[str, Any]]:
        """Check instance state for idle instances."""
        findings = []

        # States: pending, running, stopping, stopped, shutting-down, terminated
        if state in ["stopped", "stopping"]:
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-state-{state}",
                    "severity": "low",
                    "category": "cost_optimization",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "instance_state.idle",
                    "status": "warning",
                    "description": f"Instance {instance_id} is in {state} state",
                    "remediation": "Consider terminating or starting the instance based on requirements",
                }
            )
        elif state == "running":
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-state-running",
                    "severity": "info",
                    "category": "compliance",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "instance_state.running",
                    "status": "pass",
                    "description": f"Instance {instance_id} is running",
                    "remediation": "Continue monitoring instance health",
                }
            )
        else:
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-state-{state}",
                    "severity": "info",
                    "category": "compliance",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "instance_state.transition",
                    "status": "pass",
                    "description": f"Instance {instance_id} is in {state} state",
                    "remediation": "Monitor instance state transitions",
                }
            )

        return findings

    def _check_root_volume_encryption(
        self, instance_id: str, instance_name: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Check if root EBS volume is encrypted."""
        findings = []

        try:
            # Get block device mappings
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            block_devices = response["Reservations"][0]["Instances"][0].get(
                "BlockDeviceMappings", []
            )

            for device in block_devices:
                # Check if this is root volume (usually /dev/sda1 or /dev/xvda)
                device_name = device.get("DeviceName", "")
                if "sda1" in device_name or "xvda" in device_name:
                    volume_id = device.get("Ebs", {}).get("VolumeId")

                    if volume_id:
                        volume_response = self.ec2_client.describe_volumes(
                            VolumeIds=[volume_id]
                        )
                        volume = volume_response["Volumes"][0]
                        encrypted = volume.get("Encrypted", False)

                        if encrypted:
                            findings.append(
                                {
                                    "finding_id": f"ec2-{instance_id[-8:]}-root-enc",
                                    "severity": "info",
                                    "category": "security",
                                    "resource_type": "instance",
                                    "resource_id": instance_id,
                                    "resource_name": instance_name,
                                    "check_name": "root_volume.encrypted",
                                    "status": "pass",
                                    "description": f"Root volume {volume_id} for instance {instance_id} is encrypted",
                                    "remediation": "Keep encryption enabled",
                                }
                            )
                        else:
                            findings.append(
                                {
                                    "finding_id": f"ec2-{instance_id[-8:]}-root-noenc",
                                    "severity": "high",
                                    "category": "security",
                                    "resource_type": "instance",
                                    "resource_id": instance_id,
                                    "resource_name": instance_name,
                                    "check_name": "root_volume.unencrypted",
                                    "status": "fail",
                                    "description": f"Root volume {volume_id} for instance {instance_id} is NOT encrypted",
                                    "remediation": "Encrypt root volume or create new encrypted instance",
                                }
                            )
                    break

        except Exception as e:
            logger.warning(
                f"Could not check root volume encryption for {instance_id}: {e}"
            )
            findings.append(
                {
                    "finding_id": f"ec2-{instance_id[-8:]}-root-enc-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "instance",
                    "resource_id": instance_id,
                    "resource_name": instance_name,
                    "check_name": "root_volume.encrypted.error",
                    "status": "warning",
                    "description": f"Could not verify root volume encryption: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeInstances and ec2:DescribeVolumes",
                }
            )

        return findings

    def _check_orphaned_volume(
        self,
        volume_id: str,
        volume_name: Optional[str],
        volume_state: str,
        volume_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check for orphaned volumes (available state, not attached)."""
        findings = []

        try:
            attachments = volume_data.get("Attachments", [])

            if volume_state == "available" and not attachments:
                # Check volume age
                create_time = volume_data.get("CreateTime", datetime.utcnow())
                age_days = (datetime.utcnow() - create_time).days

                findings.append(
                    {
                        "finding_id": f"ec2-{volume_id[-8:]}-orphan",
                        "severity": "medium",
                        "category": "cost_optimization",
                        "resource_type": "volume",
                        "resource_id": volume_id,
                        "resource_name": volume_name,
                        "check_name": "volume.orphaned",
                        "status": "warning",
                        "description": f"Volume {volume_id} is in 'available' state and not attached (orphaned). Age: {age_days} days.",
                        "remediation": "Review and delete orphaned volumes to reduce costs",
                    }
                )
            elif volume_state == "in-use":
                findings.append(
                    {
                        "finding_id": f"ec2-{volume_id[-8:]}-inuse",
                        "severity": "info",
                        "category": "compliance",
                        "resource_type": "volume",
                        "resource_id": volume_id,
                        "resource_name": volume_name,
                        "check_name": "volume.in_use",
                        "status": "pass",
                        "description": f"Volume {volume_id} is attached to an instance",
                        "remediation": "Continue monitoring volume usage",
                    }
                )

        except Exception as e:
            logger.warning(
                f"Could not check orphaned status for volume {volume_id}: {e}"
            )
            findings.append(
                {
                    "finding_id": f"ec2-{volume_id[-8:]}-orphan-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "volume",
                    "resource_id": volume_id,
                    "resource_name": volume_name,
                    "check_name": "volume.orphaned.error",
                    "status": "warning",
                    "description": f"Could not verify orphaned status: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeVolumes",
                }
            )

        return findings

    def _check_volume_encryption(
        self, volume_id: str, volume_name: Optional[str], volume_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check if volume is encrypted."""
        findings = []

        try:
            encrypted = volume_data.get("Encrypted", False)

            if encrypted:
                findings.append(
                    {
                        "finding_id": f"ec2-{volume_id[-8:]}-enc",
                        "severity": "info",
                        "category": "security",
                        "resource_type": "volume",
                        "resource_id": volume_id,
                        "resource_name": volume_name,
                        "check_name": "volume.encrypted",
                        "status": "pass",
                        "description": f"Volume {volume_id} is encrypted",
                        "remediation": "Keep encryption enabled",
                    }
                )
            else:
                findings.append(
                    {
                        "finding_id": f"ec2-{volume_id[-8:]}-noenc",
                        "severity": "high",
                        "category": "security",
                        "resource_type": "volume",
                        "resource_id": volume_id,
                        "resource_name": volume_name,
                        "check_name": "volume.unencrypted",
                        "status": "fail",
                        "description": f"Volume {volume_id} is NOT encrypted",
                        "remediation": "Create snapshot and create new encrypted volume",
                    }
                )

        except Exception as e:
            logger.warning(f"Could not check encryption for volume {volume_id}: {e}")
            findings.append(
                {
                    "finding_id": f"ec2-{volume_id[-8:]}-enc-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "volume",
                    "resource_id": volume_id,
                    "resource_name": volume_name,
                    "check_name": "volume.encrypted.error",
                    "status": "warning",
                    "description": f"Could not verify encryption: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeVolumes",
                }
            )

        return findings

    def _check_volume_age(
        self, volume_id: str, volume_name: Optional[str], volume_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check volume age."""
        findings = []

        try:
            create_time = volume_data.get("CreateTime", datetime.utcnow())
            age_days = (datetime.utcnow() - create_time).days

            if age_days > 365:
                findings.append(
                    {
                        "finding_id": f"ec2-{volume_id[-8:]}-age-old",
                        "severity": "medium",
                        "category": "compliance",
                        "resource_type": "volume",
                        "resource_id": volume_id,
                        "resource_name": volume_name,
                        "check_name": "volume.age",
                        "status": "warning",
                        "description": f"Volume {volume_id} is {age_days} days old",
                        "remediation": "Review old volumes for continued necessity",
                    }
                )
            else:
                findings.append(
                    {
                        "finding_id": f"ec2-{volume_id[-8:]}-age-{age_days}d",
                        "severity": "info",
                        "category": "compliance",
                        "resource_type": "volume",
                        "resource_id": volume_id,
                        "resource_name": volume_name,
                        "check_name": "volume.age",
                        "status": "pass",
                        "description": f"Volume {volume_id} is {age_days} days old",
                        "remediation": "Keep track of volume age for lifecycle management",
                    }
                )

        except Exception as e:
            logger.warning(f"Could not check volume age for {volume_id}: {e}")
            findings.append(
                {
                    "finding_id": f"ec2-{volume_id[-8:]}-age-error",
                    "severity": "medium",
                    "category": "error",
                    "resource_type": "volume",
                    "resource_id": volume_id,
                    "resource_name": volume_name,
                    "check_name": "volume.age.error",
                    "status": "warning",
                    "description": f"Could not verify volume age: {str(e)}",
                    "remediation": "Check permissions for ec2:DescribeVolumes",
                }
            )

        return findings

    def _get_instance_name(self, instance_data: Dict[str, Any]) -> Optional[str]:
        """Extract instance name from tags."""
        tags = instance_data.get("Tags", [])
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value")
        return None

    def _get_volume_name(self, volume_data: Dict[str, Any]) -> Optional[str]:
        """Extract volume name from tags."""
        tags = volume_data.get("Tags", [])
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value")
        return None

    def _get_security_group_rules(self, sg_id: str) -> List[Dict[str, Any]]:
        """Get security group rules."""
        try:
            response = self.ec2_client.describe_security_groups(GroupIds=[sg_id])
            sg = response["SecurityGroups"][0]
            return sg.get("IpPermissions", [])
        except Exception as e:
            logger.warning(f"Could not get security group rules for {sg_id}: {e}")
            return []

    def get_findings_summary(self) -> Dict[str, Any]:
        """Get summary of findings."""
        if not self.findings:
            return {
                "total_findings": 0,
                "by_severity": {},
                "by_category": {},
                "summary": "No findings yet. Run scan_all_instances() or scan_all_volumes() first.",
            }

        by_severity = {}
        by_category = {}

        for finding in self.findings:
            severity = finding.get("severity", "unknown")
            category = finding.get("category", "unknown")

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total_findings": len(self.findings),
            "by_severity": by_severity,
            "by_category": by_category,
            "findings": self.findings,
        }

    def save_scan_results(self) -> bool:
        """Save scan results to session manager."""
        results = {
            "scan_type": "ec2",
            "tenant_id": self.tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "findings": self.findings,
            "summary": self.get_findings_summary(),
        }

        return self.session_manager.save_session(f"ec2_scan_{self.tenant_id}", results)
