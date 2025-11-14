"""Bulk operations for Facebook leads - batch processing"""

from app import db
from app.models.meta_lead import FacebookLead, LeadInteraction
from app.models.user import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BulkLeadOperations:
    """Handle bulk operations on multiple leads"""
    
    @staticmethod
    def bulk_status_change(lead_ids, new_status, user_id):
        """Change status for multiple leads at once"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'Kullanıcı bulunamadı', 'updated': 0}
            
            valid_statuses = ['new', 'assigned', 'contacted', 'converted', 'rejected']
            if new_status not in valid_statuses:
                return {'success': False, 'message': 'Geçersiz durum', 'updated': 0}
            
            # Get leads
            leads = FacebookLead.query.filter(FacebookLead.id.in_(lead_ids)).all()
            
            if not leads:
                return {'success': False, 'message': 'Lead bulunamadı', 'updated': 0}
            
            updated_count = 0
            errors = []
            
            for lead in leads:
                try:
                    old_status = lead.status
                    lead.status = new_status
                    lead.updated_at = datetime.utcnow()
                    
                    # Create interaction record
                    interaction = LeadInteraction(
                        lead_id=lead.id,
                        user_id=user_id,
                        interaction_type='status_changed',
                        description=f"{old_status} → {new_status} (Toplu İşlem)",
                        result='success'
                    )
                    
                    db.session.add(interaction)
                    updated_count += 1
                
                except Exception as e:
                    logger.error(f"Bulk status change error for lead {lead.id}: {str(e)}")
                    errors.append(f"Lead {lead.id}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{updated_count} lead durumu güncellendi',
                'updated': updated_count,
                'errors': errors
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk status change failed: {str(e)}")
            return {'success': False, 'message': str(e), 'updated': 0}
    
    @staticmethod
    def bulk_assign(lead_ids, user_id, assign_to_user_id):
        """Assign multiple leads to a user"""
        try:
            assign_user = User.query.get(assign_to_user_id)
            if not assign_user:
                return {'success': False, 'message': 'Personel bulunamadı', 'updated': 0}
            
            # Get leads
            leads = FacebookLead.query.filter(FacebookLead.id.in_(lead_ids)).all()
            
            if not leads:
                return {'success': False, 'message': 'Lead bulunamadı', 'updated': 0}
            
            updated_count = 0
            
            for lead in leads:
                try:
                    lead.assigned_to_id = assign_to_user_id
                    lead.status = 'assigned'
                    lead.updated_at = datetime.utcnow()
                    
                    interaction = LeadInteraction(
                        lead_id=lead.id,
                        user_id=user_id,
                        interaction_type='status_changed',
                        description=f"Toplu atama: {assign_user.username}",
                        result='success'
                    )
                    
                    db.session.add(interaction)
                    updated_count += 1
                
                except Exception as e:
                    logger.error(f"Bulk assign error for lead {lead.id}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{updated_count} lead {assign_user.username} kullanıcısına atandı',
                'updated': updated_count
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk assign failed: {str(e)}")
            return {'success': False, 'message': str(e), 'updated': 0}
    
    @staticmethod
    def bulk_delete(lead_ids, user_id):
        """Delete multiple leads"""
        try:
            # Get leads
            leads = FacebookLead.query.filter(FacebookLead.id.in_(lead_ids)).all()
            
            if not leads:
                return {'success': False, 'message': 'Lead bulunamadı', 'deleted': 0}
            
            deleted_count = 0
            
            for lead in leads:
                try:
                    # Delete interactions first
                    LeadInteraction.query.filter_by(lead_id=lead.id).delete()
                    
                    # Log deletion
                    interaction = LeadInteraction(
                        lead_id=lead.id,
                        user_id=user_id,
                        interaction_type='note',
                        description='Lead silinmiş (Toplu İşlem)',
                        result='success'
                    )
                    db.session.add(interaction)
                    
                    # Delete lead
                    db.session.delete(lead)
                    deleted_count += 1
                
                except Exception as e:
                    logger.error(f"Bulk delete error for lead {lead.id}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{deleted_count} lead silindi',
                'deleted': deleted_count
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk delete failed: {str(e)}")
            return {'success': False, 'message': str(e), 'deleted': 0}
    
    @staticmethod
    def bulk_add_tag(lead_ids, tag_text, user_id):
        """Add a tag/note to multiple leads"""
        try:
            leads = FacebookLead.query.filter(FacebookLead.id.in_(lead_ids)).all()
            
            if not leads:
                return {'success': False, 'message': 'Lead bulunamadı', 'updated': 0}
            
            updated_count = 0
            
            for lead in leads:
                try:
                    interaction = LeadInteraction(
                        lead_id=lead.id,
                        user_id=user_id,
                        interaction_type='note',
                        description=tag_text,
                        result='success'
                    )
                    
                    db.session.add(interaction)
                    updated_count += 1
                
                except Exception as e:
                    logger.error(f"Bulk tag error for lead {lead.id}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{updated_count} lead\'e tag eklendi',
                'updated': updated_count
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk tag failed: {str(e)}")
            return {'success': False, 'message': str(e), 'updated': 0}
    
    @staticmethod
    def export_leads(lead_ids, format='csv'):
        """Export leads to CSV or Excel"""
        import csv
        from io import StringIO
        
        leads = FacebookLead.query.filter(FacebookLead.id.in_(lead_ids)).all()
        
        if not leads:
            return None
        
        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow([
                'ID', 'Ad Soyad', 'Email', 'Telefon', 'Dağıtıcı', 
                'Durum', 'Atanan Kişi', 'Oluşturulma Tarihi'
            ])
            
            # Rows
            for lead in leads:
                writer.writerow([
                    lead.id,
                    lead.full_name(),
                    lead.email,
                    lead.phone,
                    lead.distributor.name,
                    lead.status,
                    lead.assigned_to.username if lead.assigned_to else '',
                    lead.created_at.strftime('%d.%m.%Y %H:%M')
                ])
            
            return output.getvalue()
        
        elif format == 'json':
            import json
            return json.dumps(
                [lead.to_dict() for lead in leads],
                ensure_ascii=False,
                indent=2
            )
        
        return None
