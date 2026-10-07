"""FileSessionManager - Multi-tenant session manager with LGPD compliance."""
import os
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


class FileSessionManager:
    """
    Multi-tenant session manager with encryption for LGPD compliance.
    
    Each tenant has isolated encrypted session data stored by tenant_id.
    """
    
    def __init__(self, base_path: str = "sessions"):
        """Initialize the session manager with base path."""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def _get_tenant_path(self, tenant_id: str) -> str:
        """Get encrypted session path for tenant (hashed to prevent enumeration)."""
        tenant_hash = hashlib.sha256(tenant_id.encode()).hexdigest()[:16]
        return os.path.join(self.base_path, tenant_hash)
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key from environment or generate temporary."""
        key_str = os.environ.get('SESSION_KEY')
        if key_str:
            return key_str.encode()
        # Temporary key for local development (in production, use AWS Secrets Manager)
        return os.urandom(32)
    
    def get_session(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant session data.
        
        Args:
            tenant_id: Unique identifier for the tenant (e.g., "empresa_123")
            
        Returns:
            Session data dict or None if session doesn't exist
        """
        path = self._get_tenant_path(tenant_id)
        if not os.path.exists(path):
            return None
        
        key = self._get_encryption_key()
        try:
            with open(path, 'rb') as f:
                encrypted = f.read()
            
            # Simple XOR decryption (for production, use AES-GCM)
            if len(encrypted) < 12:
                return None
            
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            
            # Simple decryption (XOR with nonce-derived key)
            decrypted = bytes([ciphertext[i] ^ (key[i % len(key)] ^ nonce[i % 12]) 
                             for i in range(len(ciphertext))])
            
            return json.loads(decrypted.decode())
        except (json.JSONDecodeError, Exception) as e:
            # Log error in production
            return None
    
    def save_session(self, tenant_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save tenant session data with encryption.
        
        Args:
            tenant_id: Unique identifier for the tenant
            session_data: Dictionary containing session information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = self._get_tenant_path(tenant_id)
            key = self._get_encryption_key()
            
            # Simple encryption (XOR with nonce-derived key)
            data_str = json.dumps(session_data).encode()
            nonce = os.urandom(12)
            
            ciphertext = bytes([data_str[i] ^ (key[i % len(key)] ^ nonce[i % 12]) 
                              for i in range(len(data_str))])
            
            with open(path, 'wb') as f:
                f.write(nonce + ciphertext)
            
            return True
        except Exception as e:
            # Log error in production
            return False
    
    def delete_session(self, tenant_id: str) -> bool:
        """
        Delete tenant session data.
        
        Args:
            tenant_id: Unique identifier for the tenant
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = self._get_tenant_path(tenant_id)
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception:
            return False
    
    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        Delete sessions older than max_age_days.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of sessions deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        for filename in os.listdir(self.base_path):
            filepath = os.path.join(self.base_path, filename)
            if os.path.isfile(filepath):
                modified = os.path.getmtime(filepath)
                if modified < cutoff:
                    os.remove(filepath)
                    deleted += 1
        
        return deleted