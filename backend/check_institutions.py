#!/usr/bin/env python3
"""
Helper script to check and create institutions for bulk upload testing.
Run this from the backend directory.
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.engine import SessionLocal
from app.models.institution import Institution

def check_and_create_institutions():
    """Check existing institutions and create test ones if needed."""
    db = SessionLocal()

    try:
        # Get all existing institutions
        existing = db.query(Institution).all()
        print(f"\n📊 Existing institutions ({len(existing)}):")
        for inst in existing:
            print(f"  - {inst.name} ({inst.type})")

        # Define test institutions from the sample CSV
        test_institutions = [
            {
                "name": "PLAI BMD",
                "type": "Corporate",
                "total_users": 50,
                "contact_email": "plai-bmd@example.com",
                "contact_person": "Admin PLAI",
                "status": "ACTIVE"
            },
            {
                "name": "SMP Budi Mulia Dua",
                "type": "School",
                "total_users": 100,
                "contact_email": "smp-budi-mulia@example.com",
                "contact_person": "Admin SMP",
                "status": "ACTIVE"
            },
            {
                "name": "SD Budi Mulia Dua Panjen",
                "type": "School",
                "total_users": 80,
                "contact_email": "sd-budi-mulia@example.com",
                "contact_person": "Admin SD",
                "status": "ACTIVE"
            }
        ]

        # Check and create test institutions
        created_count = 0
        for inst_data in test_institutions:
            existing_inst = db.query(Institution).filter(
                Institution.name == inst_data["name"]
            ).first()

            if not existing_inst:
                new_inst = Institution(**inst_data)
                db.add(new_inst)
                created_count += 1
                print(f"✅ Created institution: {inst_data['name']}")
            else:
                print(f"ℹ️  Institution already exists: {inst_data['name']}")

        if created_count > 0:
            db.commit()
            print(f"\n✅ Successfully created {created_count} test institution(s)")
        else:
            print(f"\n✅ All test institutions already exist")

        print("\n🎯 You can now use the sample CSV files for bulk upload!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_create_institutions()
