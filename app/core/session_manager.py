"""Local file storage for tenant-scoped session data."""

import glob
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

_LOCAL_SESSION_KEY = os.urandom(32)


class FileSessionManager:
    """Store session records under tenant-scoped file names.

    The XOR transformation is only obfuscation, not secure encryption.
    """

    def __init__(self, base_path: str = "sessions"):
        """Initialize the session manager with base path."""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_tenant_path(self, tenant_id: str) -> str:
        """Return a tenant-scoped path using a truncated tenant hash."""
        tenant_hash = hashlib.sha256(tenant_id.encode()).hexdigest()[:16]
        return os.path.join(self.base_path, tenant_hash)

    def _get_session_path(
        self, tenant_id: str, session_id: Optional[str] = None
    ) -> str:
        tenant_path = self._get_tenant_path(tenant_id)
        if session_id is None:
            return tenant_path
        session_hash = hashlib.sha256(session_id.encode()).hexdigest()[:16]
        return f"{tenant_path}.{session_hash}"

    def _get_storage_key(self) -> bytes:
        """Get the configured key or a process-local key for local use."""
        key_str = os.environ.get("SESSION_KEY")
        if key_str:
            return key_str.encode()
        # A process-local key keeps local API requests readable without a configured key.
        return _LOCAL_SESSION_KEY

    def get_session(
        self, tenant_id: str, session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant session data.

        Args:
            tenant_id: Unique identifier for the tenant (e.g., "empresa_123")

        Returns:
            Session data dict or None if session doesn't exist
        """
        path = self._get_session_path(tenant_id, session_id)
        if not os.path.exists(path):
            return None

        return self._read_session(path)

    def _read_session(self, path: str) -> Optional[Dict[str, Any]]:
        key = self._get_storage_key()
        try:
            with open(path, "rb") as f:
                encrypted = f.read()

            # XOR is retained for compatibility; it does not provide encryption.
            if len(encrypted) < 12:
                return None

            nonce = encrypted[:12]
            ciphertext = encrypted[12:]

            # Reverse the storage obfuscation.
            decrypted = bytes(
                [
                    ciphertext[i] ^ (key[i % len(key)] ^ nonce[i % 12])
                    for i in range(len(ciphertext))
                ]
            )

            return json.loads(decrypted.decode())
        except (json.JSONDecodeError, Exception):
            # Log error in production
            return None

    def save_session(
        self,
        tenant_id: str,
        session_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Save tenant session data using the local storage transformation.

        Args:
            tenant_id: Unique identifier for the tenant
            session_data: Dictionary containing session information

        Returns:
            True if successful, False otherwise
        """
        try:
            path = self._get_session_path(tenant_id, session_id)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            key = self._get_storage_key()

            # XOR only obfuscates the serialized session data.
            data_str = json.dumps(session_data).encode()
            nonce = os.urandom(12)

            ciphertext = bytes(
                [
                    data_str[i] ^ (key[i % len(key)] ^ nonce[i % 12])
                    for i in range(len(data_str))
                ]
            )

            with open(path, "wb") as f:
                f.write(nonce + ciphertext)

            return True
        except Exception:
            # Log error in production
            return False

    def list_sessions(self, tenant_id: str) -> list[Dict[str, Any]]:
        """Load all named session records for one tenant."""
        tenant_path = self._get_tenant_path(tenant_id)
        records = []
        for path in glob.glob(f"{tenant_path}.*"):
            record = self._read_session(path)
            if record is not None:
                records.append(record)
        return records

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
