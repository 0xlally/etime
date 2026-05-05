"""Security tests for database bootstrap defaults."""
import pytest

from app.core.config import Settings, settings
from app.core.init_db import ensure_default_admin
from app.models.user import User, UserRole
from app.utils.security import verify_password


def test_settings_do_not_auto_seed_default_admin(monkeypatch):
    monkeypatch.delenv("AUTO_INIT_ADMIN", raising=False)
    monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

    config = Settings(_env_file=None)

    assert config.AUTO_INIT_ADMIN is False
    assert config.DEFAULT_ADMIN_PASSWORD is None


def test_default_admin_seed_rejects_known_default_password(monkeypatch, db_session):
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_PASSWORD", "admin123")

    with pytest.raises(ValueError, match="known default"):
        ensure_default_admin(db_session)

    assert db_session.query(User).filter(User.username == "admin").first() is None


def test_default_admin_seed_requires_strong_explicit_password(monkeypatch, db_session):
    password = "local-admin-pass-2026"
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_USERNAME", "localadmin")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_EMAIL", "localadmin@example.com")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_PASSWORD", password)

    admin, created, updated = ensure_default_admin(db_session)

    assert created is True
    assert updated is False
    assert admin.role == UserRole.ADMIN.value
    assert verify_password(password, admin.password_hash)
