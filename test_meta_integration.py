#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for Meta/Facebook Lead integration"""

import sys
import io
import os

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import Distributor
from app.models.meta_lead import MetaAPIConfig, FacebookLead, LeadInteraction
from app.services.meta_lead_service import MetaLeadService

app = create_app()

def test_meta_integration():
    """Test Meta API integration"""
    with app.app_context():
        print("\n" + "="*60)
        print("Meta/Facebook Lead Integration Test")
        print("="*60)
        
        # 1. Check if distributor exists
        print("\n[1] Checking distributors...")
        distributors = Distributor.query.all()
        if not distributors:
            print("   ERROR: No distributors found")
            return
        
        distributor = distributors[0]
        print(f"   OK: Found distributor: {distributor.name} (ID: {distributor.id})")
        
        # 2. Create Meta API Config
        print("\n[2] Checking Meta API Config...")
        meta_config = MetaAPIConfig.query.filter_by(distributor_id=distributor.id).first()
        
        if not meta_config:
            print(f"   Creating new Meta API Config for {distributor.name}...")
            meta_config = MetaAPIConfig(
                distributor_id=distributor.id,
                page_id='TEST_PAGE_ID_123',
                form_id='TEST_FORM_ID_456',
                access_token='TEST_TOKEN_EAAXXXXX',
                is_active=True,
                fetch_interval_minutes=5
            )
            db.session.add(meta_config)
            db.session.commit()
            print(f"   OK: Created config (ID: {meta_config.id})")
        else:
            print(f"   OK: Config exists (ID: {meta_config.id})")
        
        # 3. Test creating test leads
        print("\n[3] Creating test Facebook leads...")
        test_leads_data = [
            {
                'id': 'fb_lead_001',
                'created_time': '2025-01-21T10:30:00Z',
                'field_data': [
                    {'name': 'first_name', 'values': ['Ahmet']},
                    {'name': 'last_name', 'values': ['Kaya']},
                    {'name': 'email', 'values': ['ahmet@example.com']},
                    {'name': 'phone_number', 'values': ['+905551234567']},
                    {'name': 'interested_service', 'values': ['hair_transplant']}
                ]
            },
            {
                'id': 'fb_lead_002',
                'created_time': '2025-01-21T11:15:00Z',
                'field_data': [
                    {'name': 'first_name', 'values': ['Fatma']},
                    {'name': 'last_name', 'values': ['Çetin']},
                    {'name': 'email', 'values': ['fatma@example.com']},
                    {'name': 'phone_number', 'values': ['+905559876543']},
                    {'name': 'interested_service', 'values': ['aesthetic_surgery']}
                ]
            }
        ]
        
        service = MetaLeadService(meta_config)
        
        # Parse and store leads
        stored_count = 0
        for lead_data in test_leads_data:
            parsed = service.parse_lead_data(lead_data)
            if parsed:
                # Check if exists
                existing = FacebookLead.query.filter_by(
                    meta_lead_id=parsed['meta_lead_id']
                ).first()
                
                if not existing:
                    new_lead = FacebookLead(
                        distributor_id=distributor.id,
                        meta_lead_id=parsed.get('meta_lead_id'),
                        first_name=parsed.get('first_name', ''),
                        last_name=parsed.get('last_name', ''),
                        email=parsed.get('email', ''),
                        phone=parsed.get('phone', ''),
                        form_data=parsed.get('form_data', {}),
                        status='new'
                    )
                    db.session.add(new_lead)
                    stored_count += 1
                    print(f"   OK: Created lead: {new_lead.full_name()} ({new_lead.email})")
        
        db.session.commit()
        print(f"   OK: Total leads created: {stored_count}")
        
        # 4. Display all leads
        print("\n[4] All Facebook leads in system:")
        all_leads = FacebookLead.query.filter_by(distributor_id=distributor.id).all()
        if all_leads:
            for lead in all_leads:
                print(f"   - {lead.full_name():20} | {lead.email:30} | {lead.status:10}")
        else:
            print("   No leads found")
        
        # 5. Test status update
        print("\n[5] Testing status update...")
        if all_leads:
            lead = all_leads[0]
            from app.models.user import User
            user = User.query.first()
            
            if user:
                old_status = lead.status
                lead.status = 'contacted'
                
                interaction = LeadInteraction(
                    lead_id=lead.id,
                    user_id=user.id,
                    interaction_type='status_changed',
                    description=f"{old_status} -> contacted",
                    result='success'
                )
                db.session.add(interaction)
                db.session.commit()
                print(f"   OK: Updated lead status: {old_status} -> contacted")
        
        # 6. Display statistics
        print("\n[6] Statistics:")
        print(f"   - Total leads: {FacebookLead.query.filter_by(distributor_id=distributor.id).count()}")
        print(f"   - New leads: {FacebookLead.query.filter_by(distributor_id=distributor.id, status='new').count()}")
        print(f"   - Contacted: {FacebookLead.query.filter_by(distributor_id=distributor.id, status='contacted').count()}")
        print(f"   - Converted: {FacebookLead.query.filter_by(distributor_id=distributor.id, status='converted').count()}")
        print(f"   - Total interactions: {LeadInteraction.query.count()}")
        
        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("1. Go to Admin Panel -> Facebook Leads")
        print("2. Configure Meta API credentials for distributors")
        print("3. Test connection and sync leads")
        print("4. View and manage leads in the dashboard")
        print("="*60 + "\n")

if __name__ == '__main__':
    try:
        test_meta_integration()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
