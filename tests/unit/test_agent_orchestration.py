"""Unit tests for Agent orchestration."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.audit_agent import AuditAgent, AuditJob
from datetime import datetime


class TestAuditAgent:
    """Test Audit Agent orchestration."""
    
    def test_init(self):
        """Test agent initialization."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        assert agent.tenant_id == "test_tenant"
        assert agent.region == "us-east-1"
        assert agent.jobs == {}
    
    def test_start_audit_default_scanners(self):
        """Test starting audit with default scanners."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        # Mock the scanners to avoid AWS calls
        with patch.object(agent, '_run_audit') as mock_run:
            mock_run.return_value = {
                'job_id': 'test123',
                'tenant_id': 'test_tenant',
                'status': 'completed',
                'scanners': ['s3', 'iam', 'ec2', 'security_group'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = agent.start_audit()
            
            assert 'job_id' in result
            assert result['status'] == 'completed'
    
    def test_start_audit_specific_scanners(self):
        """Test starting audit with specific scanners."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        # Mock the scanners to avoid AWS calls
        with patch.object(agent, '_run_audit') as mock_run:
            mock_run.return_value = {
                'job_id': 'test456',
                'tenant_id': 'test_tenant',
                'status': 'completed',
                'scanners': ['s3'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = agent.start_audit(scanners=['s3'])
            
            assert 's3' in result['scanners']
            assert len(result['scanners']) == 1
    
    def test_available_scanners(self):
        """Test available scanners list."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        assert 's3' in agent.SCANNERS
        assert 'iam' in agent.SCANNERS
        assert 'ec2' in agent.SCANNERS
        assert 'security_group' in agent.SCANNERS
    
    def test_job_status_tracking(self):
        """Test job status tracking."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        # Create a mock job
        job = AuditJob(
            job_id='test123',
            tenant_id='test_tenant',
            status='pending',
            scanners=['s3']
        )
        
        agent.jobs['test123'] = job
        
        # Get job status
        result = agent.get_job_status('test123')
        
        assert result['job_id'] == 'test123'
        assert result['status'] == 'pending'
    
    def test_list_jobs(self):
        """Test listing jobs."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        # Add mock jobs
        job1 = AuditJob(job_id='job1', tenant_id='test_tenant', status='completed', scanners=['s3'])
        job2 = AuditJob(job_id='job2', tenant_id='test_tenant', status='running', scanners=['iam'])
        
        agent.jobs['job1'] = job1
        agent.jobs['job2'] = job2
        
        jobs = agent.list_jobs()
        
        assert len(jobs) == 2
        assert jobs[0]['job_id'] in ['job1', 'job2']
        assert jobs[1]['job_id'] in ['job1', 'job2']


class TestAuditJobDataclass:
    """Test AuditJob dataclass."""
    
    def test_job_creation(self):
        """Test creating a job."""
        job = AuditJob(
            job_id='test123',
            tenant_id='tenant_1',
            status='pending',
            scanners=['s3', 'iam']
        )
        
        assert job.job_id == 'test123'
        assert job.tenant_id == 'tenant_1'
        assert job.status == 'pending'
        assert 's3' in job.scanners
        assert 'iam' in job.scanners
    
    def test_job_with_results(self):
        """Test job with results."""
        job = AuditJob(
            job_id='test456',
            tenant_id='tenant_2',
            status='completed',
            scanners=['s3'],
            findings_count=10,
            findings_by_severity={'critical': 1, 'high': 2, 'medium': 3, 'low': 4},
            results={'s3': {'findings': [], 'summary': {}}}
        )
        
        assert job.findings_count == 10
        assert job.findings_by_severity['critical'] == 1
        assert 's3' in job.results


class TestAgentOrchestration:
    """Test agent orchestration scenarios."""
    
    def test_multi_scanner_execution(self):
        """Test running multiple scanners."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        # All scanners should be available
        assert len(agent.SCANNERS) == 4
        
        # Mock each scanner to return empty findings
        with patch('app.agents.s3_scanner.S3Scanner') as mock_s3, \
             patch('app.agents.iam_scanner.IAMScanner') as mock_iam, \
             patch('app.agents.ec2_scanner.EC2Scanner') as mock_ec2, \
             patch('app.agents.security_group_scanner.SecurityGroupScanner') as mock_sg:
            
            # Configure mocks
            mock_s3.return_value.scan_all_buckets.return_value = []
            mock_iam.return_value.scan_all_users.return_value = []
            mock_iam.return_value.scan_all_roles.return_value = []
            mock_ec2.return_value.scan_all_instances.return_value = []
            mock_ec2.return_value.scan_all_volumes.return_value = []
            mock_sg.return_value.scan_all_security_groups.return_value = []
            
            # Run audit with all scanners
            result = agent.start_audit(scanners=['s3', 'iam', 'ec2', 'security_group'])
            
            assert result['status'] == 'completed'
            assert len(result['scanners']) == 4
    
    def test_single_scanner_execution(self):
        """Test running a single scanner."""
        agent = AuditAgent(tenant_id="test_tenant", region="us-east-1")
        
        with patch('app.agents.s3_scanner.S3Scanner') as mock_s3:
            mock_s3.return_value.scan_all_buckets.return_value = []
            
            result = agent.start_audit(scanners=['s3'])
            
            assert result['status'] == 'completed'
            assert result['scanners'] == ['s3']
    
    def test_lgpd_compliance_in_agent(self):
        """Test LGPD compliance in agent findings."""
        from app.security.anonymization import lgpd_anonymize
        
        # Test anonymization
        findings = [{'description': 'User john@example.com has issues'}]
        anonymized = lgpd_anonymize({'findings': findings})
        
        assert 'john@example.com' not in anonymized['findings'][0]['description']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
