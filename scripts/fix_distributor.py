"""
Fix admin user's distributor assignment
This ensures every user has a valid distributor_id for production use
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Distributor

app = create_app()
with app.app_context():
    # Get or create distributor
    distributor = Distributor.query.first()
    if not distributor:
        distributor = Distributor(
            name="MSH Med Tour",
            email="info@mshmedtour.com",
            phone="+90 555 123 4567",
            address="İstanbul, Türkiye",
            color_hex="#7a001d"
        )
        db.session.add(distributor)
        db.session.commit()
        print(f"Created distributor: {distributor.name} (ID: {distributor.id})")
    else:
        print(f"Found existing distributor: {distributor.name} (ID: {distributor.id})")
    
    # Fix admin user
    admin = User.query.filter_by(username='admin').first()
    if admin:
        if admin.distributor_id != distributor.id:
            admin.distributor_id = distributor.id
            db.session.commit()
            print(f"Updated admin user - assigned distributor_id: {distributor.id}")
        else:
            print(f"Admin already has distributor_id: {admin.distributor_id}")
    else:
        print("Warning: No admin user found!")
    
    # Verify all users have distributor
    users_without_dist = User.query.filter_by(distributor_id=None).all()
    if users_without_dist:
        print(f"\nWarning: {len(users_without_dist)} users without distributor:")
        for u in users_without_dist:
            print(f"  - {u.username}")
            u.distributor_id = distributor.id
        db.session.commit()
        print("All users now have distributor assigned.")
    else:
        print("\nAll users have valid distributor_id ✓")
