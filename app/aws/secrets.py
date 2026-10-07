"""Secrets management for multi-tenant environment."""
import os
import boto3
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecretConfig:
    """Secret configuration."""
    name: str
    environment: str
    tenant_id: Optional[str] = None
    is_global: bool = False


class SecretsManager:
    """
    Multi-tenant secrets manager.
    
    Supports:
    - Local development (.env files)
    - AWS Secrets Manager (production)
    - Per-tenant secret isolation
    """
    
    def __init__(self, environment: str = 'local'):
        """
        Initialize secrets manager.
        
        Args:
            environment: 'local' or 'production'
        """
        self.environment = environment
        self.is_local = environment == 'local'
        self._cache: Dict[str, str] = {}
    
    def get_secret(self, name: str, tenant_id: Optional[str] = None) -> Optional[str]:
        """
        Get secret value by name.
        
        Args:
            name: Secret name (e.g., 'AWS_ACCESS_KEY_ID')
            tenant_id: Optional tenant ID for tenant-specific secrets
            
        Returns:
            Secret value or None if not found
        """
        cache_key = f"{tenant_id}:{name}" if tenant_id else name
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try tenant-specific secret first
        if tenant_id:
            tenant_secret_name = f"holocron/{tenant_id}/{name}"
            value = self._get_secret_value(tenant_secret_name)
            if value:
                self._cache[cache_key] = value
                return value
        
        # Try global secret
        value = self._get_secret_value(name)
        if value:
            self._cache[cache_key] = value
            return value
        
        # Fall back to environment variable
        env_value = os.environ.get(name)
        if env_value:
            self._cache[cache_key] = env_value
            return env_value
        
        logger.warning(f"Secret '{name}' not found")
        return None
    
    def _get_secret_value(self, name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager or local .env."""
        if self.is_local:
            return self._get_local_secret(name)
        return self._get_aws_secret(name)
    
    def _get_local_secret(self, name: str) -> Optional[str]:
        """Get secret from environment variables (local mode)."""
        return os.environ.get(name)
    
    def _get_aws_secret(self, name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId=name)
            return response['SecretString']
        except client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret '{name}' not found in Secrets Manager")
            return None
        except Exception as e:
            logger.error(f"Error getting secret '{name}': {e}")
            return None
    
    def get_encryption_key(self, tenant_id: Optional[str] = None) -> Optional[bytes]:
        """
        Get encryption key for session encryption.
        
        Args:
            tenant_id: Optional tenant ID
            
        Returns:
            Encryption key as bytes or None
        """
        key_str = self.get_secret('SESSION_ENCRYPTION_KEY', tenant_id)
        if not key_str:
            # Fallback for local development
            key_str = os.environ.get('SESSION_KEY')
        if key_str:
            return key_str.encode()
        return None
    
    def get_bedrock_api_key(self, tenant_id: Optional[str] = None) -> Optional[str]:
        """
        Get Bedrock API key for tenant.
        
        Args:
            tenant_id: Optional tenant ID
            
        Returns:
            API key or None
        """
        return self.get_secret('AWS_ACCESS_KEY_ID', tenant_id)
    
    def get_aws_region(self, tenant_id: Optional[str] = None) -> str:
        """
        Get AWS region for tenant.
        
        Args:
            tenant_id: Optional tenant ID
            
        Returns:
            AWS region (defaults to us-east-1)
        """
        return self.get_secret('AWS_DEFAULT_REGION', tenant_id) or 'us-east-1'
    
    def get_all_secrets(self, tenant_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get all secrets for a tenant.
        
        Args:
            tenant_id: Optional tenant ID
            
        Returns:
            Dictionary of secret names to values
        """
        # In production, this would list secrets from Secrets Manager
        # For now, return common secrets
        secrets = {
            'AWS_ACCESS_KEY_ID': self.get_secret('AWS_ACCESS_KEY_ID', tenant_id),
            'AWS_SECRET_ACCESS_KEY': self.get_secret('AWS_SECRET_ACCESS_KEY', tenant_id),
            'SESSION_ENCRYPTION_KEY': self.get_secret('SESSION_ENCRYPTION_KEY', tenant_id),
        }
        return {k: v for k, v in secrets.items() if v is not None}


# Example usage
if __name__ == "__main__":
    # Initialize for local development
    secrets = SecretsManager(environment='local')
    
    print("Testing local secrets...")
    access_key = secrets.get_secret('AWS_ACCESS_KEY_ID')
    print(f"Access Key (local): {access_key[:10] + '...' if access_key else 'Not set'}")
    
    # For production, use:
    # secrets = SecretsManager(environment='production')
    # tenant_key = secrets.get_secret('AWS_ACCESS_KEY_ID', tenant_id='empresa_123')