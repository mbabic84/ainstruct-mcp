from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

from ..config import settings
from ..db.models import Scope


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

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
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
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


_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
