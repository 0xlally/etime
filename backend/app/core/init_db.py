"""Database initialization helpers.

- Ensures tables exist when migrations were not run (useful for local dev).
- Creates a default admin user when enabled via settings.
"""
from typing import Tuple
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.config import settings
from app.models.user import User, UserRole
from app.utils.security import hash_password


def create_tables_if_missing() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def ensure_default_admin(db: Session) -> Tuple[User, bool, bool]:
    """Ensure a default admin account exists and is active.

    Returns a tuple of (admin_user, created, updated).
    """
    admin_username = settings.DEFAULT_ADMIN_USERNAME
    admin_email = settings.DEFAULT_ADMIN_EMAIL
    admin_password = settings.DEFAULT_ADMIN_PASSWORD

    admin = db.query(User).filter(User.username == admin_username).first()
    created = False
    updated = False

    if admin is None:
        admin = User(
            email=admin_email,
            username=admin_username,
            password_hash=hash_password(admin_password),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        created = True
    else:
        # Keep existing password unless a new account is created to avoid surprise resets.
        if admin.role != UserRole.ADMIN:
            admin.role = UserRole.ADMIN.value
            updated = True
        if not admin.is_active:
            admin.is_active = True
            updated = True
        if admin.email != admin_email:
            admin.email = admin_email
            updated = True

        if updated:
            db.commit()
            db.refresh(admin)

    return admin, created, updated


def init_database() -> None:
    """Initialize database schema and optional default admin."""
    if settings.AUTO_CREATE_TABLES:
        create_tables_if_missing()

    if settings.AUTO_INIT_ADMIN:
        db = SessionLocal()
        try:
            admin, created, updated = ensure_default_admin(db)
            if created:
                print(
                    f"Default admin created -> username={admin.username}, "
                    f"email={admin.email}"
                )
            elif updated:
                print(f"Default admin ensured -> username={admin.username}")
        except Exception as exc:  # pragma: no cover - defensive logging
            db.rollback()
            print(f"Failed to ensure default admin: {exc}")
            raise
        finally:
            db.close()
