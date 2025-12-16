"""Simple database migration script - creates all tables"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import engine, Base
from app.models.user import User  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.work_target import WorkTarget  # noqa: F401
from app.models.work_evaluation import WorkEvaluation  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.punishment_event import PunishmentEvent  # noqa: F401
from app.models.admin_audit_log import AdminAuditLog  # noqa: F401

def run_migration():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    run_migration()
