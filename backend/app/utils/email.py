"""Simple email sender using SMTP."""
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings


def send_email(to_email: str, subject: str, content: str) -> None:
    """Send a plain text email via configured SMTP server.

    Raises RuntimeError if SMTP is not configured or authentication fails.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP is not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content(content)

    if settings.SMTP_SSL:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)


def build_reset_email(to_email: str, token: str) -> tuple[str, str]:
    """Construct subject and body for reset password email."""
    subject = "ETime 账户重置密码"
    body_lines = [
        "您好，",
        "",
        "您请求了重置密码，请使用下面的重置令牌完成操作：",
        token,
        "",
        "在应用的“找回密码”页面输入邮箱、重置令牌和新密码即可完成重置。",
        "如果这不是您本人操作，请忽略此邮件。",
    ]
    return subject, "\n".join(body_lines)
