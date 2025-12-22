"""Initialize default admin account"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.init_db import create_tables_if_missing, ensure_default_admin

def init_admin():
    """Create default admin account if not exists"""
    create_tables_if_missing()
    db = SessionLocal()
    
    try:
        admin, created, updated = ensure_default_admin(db)

        print("Default admin info")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        if created:
            print("Default admin created using settings values")
            print(f"  Password: {settings.DEFAULT_ADMIN_PASSWORD}")
        elif updated:
            print("Admin existed; role/active/email updated if needed")
        else:
            print("Admin already present; no changes applied")

        print("Remember to change the default password after first login if you used the default value.")
    
    except Exception as e:
        db.rollback()
        print(f"Error creating admin account: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_admin()
