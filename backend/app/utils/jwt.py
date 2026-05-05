"""JWT token utilities"""
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.user import TokenData


RESET_PASSWORD_FINGERPRINT_CLAIM = "pwd"


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: Dictionary containing token payload data
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a new JWT refresh token (longer expiration).
    
    Args:
        data: Dictionary containing token payload data
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_reset_token(data: Dict[str, Any], expires_minutes: int = 30) -> str:
    """Create a password reset token (short-lived)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({
        "exp": expire,
        "type": "reset"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_password_reset_fingerprint(password_hash: str) -> str:
    """Bind reset tokens to the current password hash without exposing it."""
    return hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        password_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_password_reset_fingerprint(token_fingerprint: Optional[str], password_hash: str) -> bool:
    """Return True only when the reset token matches the current password hash."""
    if not isinstance(token_fingerprint, str) or not token_fingerprint:
        return False
    expected = create_password_reset_fingerprint(password_hash)
    return hmac.compare_digest(token_fingerprint, expected)


def decode_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token, returning the raw payload."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        TokenData object if valid, None otherwise
    """
    payload = decode_token_payload(token)
    if payload is None:
        return None

    user_id_str = payload.get("sub")
    role: str = payload.get("role")

    if user_id_str is None:
        return None

    # Convert user_id from string to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None

    return TokenData(user_id=user_id, role=role)


def verify_token_type(token: str, token_type: str) -> bool:
    """
    Verify that a token is of the expected type (access or refresh).
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if token type matches, False otherwise
    """
    payload = decode_token_payload(token)
    if payload is None:
        return False
    return payload.get("type") == token_type
