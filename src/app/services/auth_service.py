from datetime import datetime, timedelta

import bcrypt
import jwt

from ..config import settings
from ..db import get_pat_token_repository
from ..db.models import Scope


class AuthService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a bcrypt hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def create_access_token(
        self,
        user_id: str,
        username: str,
        email: str,
        is_superuser: bool = False,
        scopes: list[Scope] | None = None,
    ) -> str:
        if scopes is None:
            scopes = [Scope.READ, Scope.WRITE]

        import uuid
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "username": username,
            "email": email,
            "is_superuser": is_superuser,
            "scopes": [s.value for s in scopes],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": uuid.uuid4().hex,  # Unique identifier to ensure token uniqueness
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        import uuid
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": uuid.uuid4().hex,  # Unique identifier to ensure token uniqueness
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def validate_access_token(self, token: str) -> dict | None:
        payload = self.decode_token(token)
        if not payload:
            return None
        if payload.get("type") != "access":
            return None
        return payload

    def validate_refresh_token(self, token: str) -> dict | None:
        payload = self.decode_token(token)
        if not payload:
            return None
        if payload.get("type") != "refresh":
            return None
        return payload

    def get_access_token_expiry(self) -> int:
        return self.access_token_expire_minutes * 60


def verify_pat_token(token: str) -> dict | None:
    if not token:
        return None
    repo = get_pat_token_repository()
    return repo.validate(token)


def is_pat_token(token: str) -> bool:
    return token.startswith("pat_live_")


_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
