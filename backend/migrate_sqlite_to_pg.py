import argparse
import contextlib
from typing import Optional
import enum

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.session import Session, SessionSource
from app.models.work_target import WorkTarget
from app.models.work_evaluation import WorkEvaluation
from app.models.admin_audit_log import AdminAuditLog


def normalize_data(model, data: dict):
    if model is User:
        role_val = data.get("role")
        if role_val is not None:
            rv = getattr(role_val, "value", role_val)
            rv = rv.lower() if isinstance(rv, str) else str(rv).lower()
            data["role"] = "admin" if "admin" in rv else "user"
    if model is Session:
        src_val = data.get("source")
        if src_val is not None:
            sv = getattr(src_val, "value", src_val)
            sv = sv.lower() if isinstance(sv, str) else str(sv).lower()
            if sv in ("timer", "manual"):
                data["source"] = SessionSource(sv)
            else:
                data["source"] = SessionSource.TIMER
    return data


def copy_table(src_session, dst_session, model, name: str, pk_field: str = "id"):
    print(f"Copying {name} ...", flush=True)
    rows = src_session.query(model).all()
    for row in rows:
        data = {col.name: getattr(row, col.name) for col in model.__table__.columns}
        data = normalize_data(model, data)
        existing = dst_session.get(model, data.get(pk_field))
        if existing:
            continue
        if model is User and data.get("role") is not None:
            # Ensure Enum type matches target DB enum and bind as value string
            normalized_role = data["role"] if isinstance(data["role"], UserRole) else UserRole(data["role"])
            data["role"] = normalized_role.value
        if model is Session and data.get("source") is not None:
            normalized_source = data["source"] if isinstance(data["source"], SessionSource) else SessionSource(
                str(data["source"]).lower()
            )
            data["source"] = normalized_source.value
            print(f"session source raw={getattr(row, 'source', None)} -> {data['source']}")
        if model is Session:
            stmt = text(
                """
                INSERT INTO sessions (id, user_id, category_id, start_time, end_time, duration_seconds, note, source, created_at, updated_at)
                VALUES (:id, :user_id, :category_id, :start_time, :end_time, :duration_seconds, :note, CAST(:source AS sessionsource), :created_at, :updated_at)
                """
            )
            dst_session.execute(stmt, data)
        else:
            dst_session.add(model(**data))
    dst_session.commit()
    print(f"Done {name}: {len(rows)} rows", flush=True)


def main(sqlite_url: str, pg_url: str):
    src_engine = create_engine(sqlite_url)
    dst_engine = create_engine(pg_url)

    SrcSession = sessionmaker(bind=src_engine)
    DstSession = sessionmaker(bind=dst_engine)

    # Ensure target tables exist
    Base.metadata.create_all(dst_engine)

    with contextlib.ExitStack() as stack:
        src_db = stack.enter_context(SrcSession())
        dst_db = stack.enter_context(DstSession())

        copy_table(src_db, dst_db, User, "users")
        copy_table(src_db, dst_db, Category, "categories")
        copy_table(src_db, dst_db, Session, "sessions")
        copy_table(src_db, dst_db, WorkTarget, "work_targets")
        copy_table(src_db, dst_db, WorkEvaluation, "work_evaluations")
        copy_table(src_db, dst_db, AdminAuditLog, "admin_audit_logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to Postgres")
    parser.add_argument("--sqlite", default="sqlite:///./app.db", help="SQLite URL, e.g. sqlite:///./app.db")
    parser.add_argument("--pg", required=True, help="Postgres URL, e.g. postgresql+psycopg2://user:pass@localhost:5432/db")
    args = parser.parse_args()
    main(args.sqlite, args.pg)
