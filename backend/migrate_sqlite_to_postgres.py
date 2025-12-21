"""One-off migration script: copy existing SQLite data into Postgres.

Run inside backend container (DATABASE_URL points to Postgres) with the SQLite file mounted:

    docker compose run --rm \
      -v $(pwd)/backend/app.db:/data/app.db:ro \
      backend python migrate_sqlite_to_postgres.py

Optional env:
- SQLITE_PATH: path to source sqlite file (default: /data/app.db)
"""
import os
from typing import Type, Iterable
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.category import Category
from app.models.session import Session as WorkSession
from app.models.work_target import WorkTarget
from app.models.work_evaluation import WorkEvaluation
from app.models.admin_audit_log import AdminAuditLog
from app.models.notification import Notification
from app.models.punishment_event import PunishmentEvent

load_dotenv()

SQLITE_PATH = os.getenv("SQLITE_PATH", "/data/app.db")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required (Postgres target)")

source_engine = create_engine(
    f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False}
)
target_engine = create_engine(DATABASE_URL)

SourceSession = sessionmaker(bind=source_engine)
TargetSession = sessionmaker(bind=target_engine)


def to_dict(obj) -> dict:
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")}


def ensure_empty(dst, model: Type):
    count = dst.query(model).count()
    if count > 0:
        raise RuntimeError(f"Target table {model.__tablename__} is not empty (has {count} rows)")


def bulk_copy(dst, model: Type, items: Iterable):
    for item in items:
        dst.add(model(**to_dict(item)))
    dst.commit()


def reset_sequence(dst, table_name: str, pk: str = "id"):
    dst.execute(text("SELECT setval(pg_get_serial_sequence(:t, :pk), (SELECT COALESCE(MAX(id),0) FROM " + table_name + "))"), {"t": table_name, "pk": pk})
    dst.commit()


def migrate():
    src = SourceSession()
    dst = TargetSession()
    try:
        # Ensure target empty
        for model in [User, Category, WorkTarget, WorkSession, WorkEvaluation, AdminAuditLog, Notification, PunishmentEvent]:
            ensure_empty(dst, model)

        # Copy in FK-safe order
        print("Copying users...")
        users = src.query(User).all()
        bulk_copy(dst, User, users)
        reset_sequence(dst, User.__tablename__)

        print("Copying categories...")
        cats = src.query(Category).all()
        bulk_copy(dst, Category, cats)
        reset_sequence(dst, Category.__tablename__)

        print("Copying work targets...")
        targets = src.query(WorkTarget).all()
        bulk_copy(dst, WorkTarget, targets)
        reset_sequence(dst, WorkTarget.__tablename__)

        print("Copying sessions...")
        sessions = src.query(WorkSession).all()
        bulk_copy(dst, WorkSession, sessions)
        reset_sequence(dst, WorkSession.__tablename__)

        print("Copying work evaluations...")
        evals = src.query(WorkEvaluation).all()
        bulk_copy(dst, WorkEvaluation, evals)
        reset_sequence(dst, WorkEvaluation.__tablename__)

        print("Copying admin audit logs...")
        audits = src.query(AdminAuditLog).all()
        bulk_copy(dst, AdminAuditLog, audits)
        reset_sequence(dst, AdminAuditLog.__tablename__)

        print("Copying notifications...")
        notifs = src.query(Notification).all()
        bulk_copy(dst, Notification, notifs)
        reset_sequence(dst, Notification.__tablename__)

        print("Copying punishment events (if any)...")
        pevents = src.query(PunishmentEvent).all()
        bulk_copy(dst, PunishmentEvent, pevents)
        reset_sequence(dst, PunishmentEvent.__tablename__)

        print("Migration completed.")
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    migrate()
