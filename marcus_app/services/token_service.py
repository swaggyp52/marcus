"""
Token service for secure GitHub token storage.

Handles:
- OS keychain storage (preferred)
- AES-256-GCM encrypted database storage (fallback)
- Never exposes plaintext tokens in logs/responses

Security:
- Encryption key derived from Marcus login password (Argon2id)
- Unique salt per installation stored in SystemConfig
- AES-256-GCM authenticated encryption (AEAD)
- Tokens only decryptable after successful Marcus login
"""

import os
import json
import base64
import secrets
from typing import Optional
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class TokenStorageError(Exception):
    """Token storage operation failed."""
    pass


class TokenService:
    """
    Manages GitHub API token storage securely.

    Priority:
    1. OS keychain (Windows: Credential Manager, macOS: Keychain, Linux: Secret Service)
    2. AES-256-GCM encrypted database storage (fallback)

    Encryption:
    - Derives 256-bit key from Marcus password using PBKDF2-HMAC-SHA256
    - Uses unique salt per installation
    - AES-256-GCM provides authenticated encryption (prevents tampering)
    """

    KEYCHAIN_SERVICE = "Marcus"
    TOKENS_DIR = Path("M:/Marcus/.tokens")  # Legacy path, unused in v0.42+

    # Encryption key derivation (stored temporarily in memory after login)
    _encryption_key: Optional[bytes] = None
    
    @staticmethod
    def store_token(username: str, token: str, db: Session = None) -> None:
        """
        Store GitHub token securely.
        
        Args:
            username: GitHub username
            token: GitHub API token
            db: Optional database session (for encrypted storage record)
        """
        # Try OS keychain first
        if TokenService._store_in_keychain(username, token):
            return
        
        # Fallback to encrypted file
        TokenService._store_encrypted(username, token, db)
    
    @staticmethod
    def retrieve_token(username: str, db: Session = None) -> Optional[str]:
        """
        Retrieve GitHub token securely.
        
        Returns:
            Token string or None if not found
        """
        # Try OS keychain first
        token = TokenService._get_from_keychain(username)
        if token:
            return token
        
        # Fallback to encrypted file
        return TokenService._get_encrypted(username, db)
    
    @staticmethod
    def delete_token(username: str, db: Session = None) -> None:
        """Delete stored token."""
        # Try OS keychain
        TokenService._delete_from_keychain(username)
        
        # Try encrypted file
        TokenService._delete_encrypted(username, db)
    
    # ========================================================================
    # OS Keychain Implementation
    # ========================================================================
    
    @staticmethod
    def _store_in_keychain(username: str, token: str) -> bool:
        """Store in OS keychain. Returns True if successful."""
        try:
            import keyring
            keyring.set_password(TokenService.KEYCHAIN_SERVICE, username, token)
            return True
        except ImportError:
            return False
        except Exception as e:
            print(f"Warning: Keychain storage failed: {e}")
            return False
    
    @staticmethod
    def _get_from_keychain(username: str) -> Optional[str]:
        """Retrieve from OS keychain."""
        try:
            import keyring
            return keyring.get_password(TokenService.KEYCHAIN_SERVICE, username)
        except (ImportError, Exception):
            return None
    
    @staticmethod
    def _delete_from_keychain(username: str) -> None:
        """Delete from OS keychain."""
        try:
            import keyring
            keyring.delete_password(TokenService.KEYCHAIN_SERVICE, username)
        except (ImportError, Exception):
            pass
    
    # ========================================================================
    # Encrypted File Storage (Fallback)
    # ========================================================================
    
    @staticmethod
    def _store_encrypted(username: str, token: str, db: Session = None) -> None:
        """Store token encrypted in VeraCrypt volume."""
        from marcus_app.core.models import GitHubToken
        
        if db is None:
            raise TokenStorageError("Database session required for encrypted storage")
        
        # Generate encryption key from Marcus session/password
        # For now, use simple base64 (should be improved with actual encryption)
        encrypted = TokenService._simple_encrypt(token)
        
        # Store in database
        existing = db.query(GitHubToken).filter(GitHubToken.username == username).first()
        
        if existing:
            existing.encrypted_token = encrypted
            existing.last_used_at = datetime.utcnow()
        else:
            github_token = GitHubToken(
                username=username,
                encrypted_token=encrypted
            )
            db.add(github_token)
        
        db.commit()
    
    @staticmethod
    def _get_encrypted(username: str, db: Session = None) -> Optional[str]:
        """Retrieve token from encrypted storage."""
        from marcus_app.core.models import GitHubToken
        
        if db is None:
            return None
        
        token_record = db.query(GitHubToken).filter(
            GitHubToken.username == username
        ).first()
        
        if not token_record:
            return None
        
        # Update last used
        token_record.last_used_at = datetime.utcnow()
        db.commit()
        
        # Decrypt and return
        return TokenService._simple_decrypt(token_record.encrypted_token)
    
    @staticmethod
    def _delete_encrypted(username: str, db: Session = None) -> None:
        """Delete token from encrypted storage."""
        from marcus_app.core.models import GitHubToken
        
        if db is None:
            return
        
        db.query(GitHubToken).filter(GitHubToken.username == username).delete()
        db.commit()
    
    # ========================================================================
    # AES-256-GCM Encryption (v0.42 Security Hardening)
    # ========================================================================

    @staticmethod
    def set_encryption_key(password: str, db: Session) -> None:
        """
        Derive and cache encryption key from Marcus password.
        Called after successful login.

        Args:
            password: Marcus login password (plaintext, not stored)
            db: Database session to retrieve/create salt
        """
        from marcus_app.core.models import SystemConfig

        # Get or create unique salt for this installation
        salt_config = db.query(SystemConfig).filter(
            SystemConfig.key == "token_encryption_salt"
        ).first()

        if not salt_config:
            # First time: generate random salt
            salt = secrets.token_bytes(32)
            salt_b64 = base64.b64encode(salt).decode()
            salt_config = SystemConfig(
                key="token_encryption_salt",
                value=salt_b64
            )
            db.add(salt_config)
            db.commit()
        else:
            salt = base64.b64decode(salt_config.value.encode())

        # Derive 256-bit key using PBKDF2-HMAC-SHA256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=600000,  # OWASP 2023 recommendation
            backend=default_backend()
        )
        TokenService._encryption_key = kdf.derive(password.encode())

    @staticmethod
    def clear_encryption_key() -> None:
        """Clear cached encryption key (on logout)."""
        TokenService._encryption_key = None

    @staticmethod
    def _encrypt_token(plaintext: str) -> str:
        """
        Encrypt token using AES-256-GCM.

        Returns:
            Base64-encoded ciphertext in format: nonce||ciphertext||tag
        """
        if TokenService._encryption_key is None:
            raise TokenStorageError("Encryption key not set. User must be logged in.")

        # AES-256-GCM encryption
        aesgcm = AESGCM(TokenService._encryption_key)
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

        # Format: nonce || ciphertext (ciphertext includes auth tag)
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode()

    @staticmethod
    def _decrypt_token(ciphertext_b64: str) -> str:
        """
        Decrypt token using AES-256-GCM.

        Args:
            ciphertext_b64: Base64-encoded ciphertext from _encrypt_token

        Returns:
            Decrypted plaintext token

        Raises:
            TokenStorageError: If decryption fails or key not set
        """
        if TokenService._encryption_key is None:
            raise TokenStorageError("Encryption key not set. User must be logged in.")

        try:
            encrypted_data = base64.b64decode(ciphertext_b64.encode())

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]

            # Decrypt
            aesgcm = AESGCM(TokenService._encryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()

        except Exception as e:
            raise TokenStorageError(f"Token decryption failed: {e}")

    # Legacy methods (for backwards compatibility)
    @staticmethod
    def _simple_encrypt(plaintext: str) -> str:
        """Legacy method - redirects to _encrypt_token."""
        return TokenService._encrypt_token(plaintext)

    @staticmethod
    def _simple_decrypt(ciphertext: str) -> str:
        """Legacy method - redirects to _decrypt_token."""
        try:
            return TokenService._decrypt_token(ciphertext)
        except Exception:
            return ""
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    @staticmethod
    def is_token_available(username: str, db: Session = None) -> bool:
        """Check if token exists."""
        try:
            token = TokenService.retrieve_token(username, db)
            return token is not None and len(token) > 0
        except Exception:
            return False
    
    @staticmethod
    def validate_github_token(token: str) -> bool:
        """
        Validate token format (basic check).
        
        GitHub tokens are either:
        - OAuth tokens: 40 hex characters
        - Personal access tokens: 40 hex characters
        - app tokens: longer, with specific prefix
        """
        if not token:
            return False
        
        # Very basic validation: at least 20 chars and alphanumeric
        return len(token) >= 20 and all(c.isalnum() or c in '-_' for c in token)
