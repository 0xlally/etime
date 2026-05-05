"""Authentication Endpoints"""
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.db import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenResponse,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.utils.security import hash_password, verify_password
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    create_password_reset_fingerprint,
    decode_token,
    decode_token_payload,
    RESET_PASSWORD_FINGERPRINT_CLAIM,
    verify_token_type,
    verify_password_reset_fingerprint,
)
from app.utils.rate_limit import is_rate_limited
from app.utils.email import send_email, build_reset_email


logger = logging.getLogger(__name__)

router = APIRouter()


def _client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(
    key: str,
    max_attempts: int,
    window_seconds: int,
    detail: str,
) -> None:
    if is_rate_limited(key, max_attempts, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data (email, username, password)
        db: Database session
        
    Returns:
        Created user object
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=UserRole.USER.value,  # Default role uses enum value
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and return access and refresh tokens.
    
    Args:
        credentials: Login credentials (username/email and password)
        db: Database session
        
    Returns:
        Access token and refresh token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    normalized_username = credentials.username.strip().lower()
    _enforce_rate_limit(
        key=f"login:{_client_host(request)}:{normalized_username}",
        max_attempts=settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        detail="Too many login attempts. Please try again later.",
    )

    # Find user by username or email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login time
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens with user_id as string in sub claim (standard JWT practice)
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using a valid refresh token.
    
    Args:
        token_data: Refresh token
        db: Database session
        
    Returns:
        New access token and refresh token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify it's a refresh token
    if not verify_token_type(token_data.refresh_token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    new_token_data = {"sub": str(user.id), "role": user.role.value}
    new_access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Issue a reset token for password recovery and send via email."""
    normalized_email = payload.email.lower()
    _enforce_rate_limit(
        key=f"forgot-password:{_client_host(request)}:{normalized_email}",
        max_attempts=settings.PASSWORD_RESET_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds=settings.PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS,
        detail="Too many password reset requests. Please try again later.",
    )

    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        reset_token = create_reset_token({
            "sub": str(user.id),
            RESET_PASSWORD_FINGERPRINT_CLAIM: create_password_reset_fingerprint(user.password_hash),
        })
        try:
            subject, body = build_reset_email(user.email, reset_token)
            send_email(user.email, subject, body)
        except Exception as exc:  # pragma: no cover - side effect
            logger.exception("Failed to send reset email: %s", exc)
            # Do not leak SMTP errors to client; keep response generic to avoid user enumeration.
            pass

    # Always respond 200 to avoid user enumeration
    return {
        "message": "如果邮箱已注册，我们已尝试发送重置邮件（如未收到请稍后重试）",
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    _enforce_rate_limit(
        key=f"reset-password:{_client_host(request)}",
        max_attempts=settings.PASSWORD_RESET_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds=settings.PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS,
        detail="Too many password reset attempts. Please try again later.",
    )

    if not verify_token_type(payload.token, "reset"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    raw_payload = decode_token_payload(payload.token)
    token_data = decode_token(payload.token)
    if raw_payload is None or token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    if not verify_password_reset_fingerprint(
        raw_payload.get(RESET_PASSWORD_FINGERPRINT_CLAIM),
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "密码已重置，请重新登录"}
