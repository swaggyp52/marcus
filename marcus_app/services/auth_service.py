"""
Authentication service for Marcus v0.36.
Handles login, session management, and password verification.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session

from ..core.models import SystemConfig


class AuthService:
    """
    Single-user authentication with Argon2id password hashing.

    Features:
    - Argon2id password hashing (OWASP recommended)
    - Secure session tokens
    - Session expiry tracking
    - Auto-lock on idle
    """

    def __init__(self):
        self.ph = PasswordHasher()
        self.sessions: Dict[str, Dict] = {}  # In-memory sessions (stateless alternative: use JWT)
        self.session_timeout = timedelta(minutes=15)  # Auto-lock after 15 min idle

    def setup_password(self, password: str, db: Session) -> bool:
        """
        Set up the initial password (first-time setup).
        Returns True if successful.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        # Hash password with Argon2id
        password_hash = self.ph.hash(password)

        # Store in SystemConfig
        config = db.query(SystemConfig).filter(
            SystemConfig.key == "auth_password_hash"
        ).first()

        if config:
            config.value = password_hash
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                key="auth_password_hash",
                value=password_hash
            )
            db.add(config)

        db.commit()
        return True

    def verify_password(self, password: str, db: Session) -> bool:
        """
        Verify password against stored hash.
        Returns True if password is correct.
        """
        config = db.query(SystemConfig).filter(
            SystemConfig.key == "auth_password_hash"
        ).first()

        if not config:
            return False

        try:
            self.ph.verify(config.value, password)

            # Check if hash needs rehashing (Argon2 params changed)
            if self.ph.check_needs_rehash(config.value):
                config.value = self.ph.hash(password)
                db.commit()

            return True
        except VerifyMismatchError:
            return False

    def has_password_set(self, db: Session) -> bool:
        """Check if a password has been configured."""
        config = db.query(SystemConfig).filter(
            SystemConfig.key == "auth_password_hash"
        ).first()
        return config is not None

    def create_session(self, user_id: str = "default") -> str:
        """
        Create a new session and return session token.
        """
        token = secrets.token_urlsafe(32)

        self.sessions[token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }

        return token

    def validate_session(self, token: str) -> bool:
        """
        Validate session token and check if not expired.
        Updates last_activity if valid.
        """
        if token not in self.sessions:
            return False

        session = self.sessions[token]

        # Check if session expired
        elapsed = datetime.utcnow() - session["last_activity"]
        if elapsed > self.session_timeout:
            del self.sessions[token]
            return False

        # Update activity
        session["last_activity"] = datetime.utcnow()
        return True

    def invalidate_session(self, token: str):
        """Invalidate a session (logout)."""
        if token in self.sessions:
            del self.sessions[token]

    def get_session_info(self, token: str) -> Optional[Dict]:
        """Get session info for debugging/audit."""
        if token in self.sessions:
            session = self.sessions[token]
            return {
                "user_id": session["user_id"],
                "created_at": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "idle_seconds": (datetime.utcnow() - session["last_activity"]).total_seconds()
            }
        return None

    def change_password(self, old_password: str, new_password: str, db: Session) -> bool:
        """
        Change password (requires old password verification).
        """
        if not self.verify_password(old_password, db):
            return False

        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")

        return self.setup_password(new_password, db)
