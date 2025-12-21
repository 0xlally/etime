"""Initialize default admin account"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password

def init_admin():
    """Create default admin account if not exists"""
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("⚠ Admin user already exists!")
            print(f"  Username: {existing_admin.username}")
            print(f"  Email: {existing_admin.email}")
            print(f"  Role: {existing_admin.role}")
            
            # Update to admin role if not already
            if existing_admin.role != UserRole.ADMIN:
                existing_admin.role = UserRole.ADMIN
                db.commit()
                print("✓ Updated user role to ADMIN")
            return
        
        # Create new admin user
        admin_user = User(
            email="admin@example.com",
            username="admin",
            password_hash=hash_password("admin"),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✓ Default admin account created successfully!")
        print(f"  Username: admin")
        print(f"  Password: admin")
        print(f"  Email: admin@example.com")
        print(f"  Role: {admin_user.role}")
        print("\n⚠ Please change the default password after first login!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating admin account: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_admin()
