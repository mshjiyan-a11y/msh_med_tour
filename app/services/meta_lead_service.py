import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app import db
from app.models.meta_lead import MetaAPIConfig, FacebookLead, LeadInteraction

logger = logging.getLogger(__name__)


class MetaLeadService:
    """Service for managing Meta/Facebook lead integration"""
    
    BASE_URL = "https://graph.instagram.com"
    
    def __init__(self, config: MetaAPIConfig):
        """Initialize service with Meta API config"""
        self.config = config
        self.api_url = f"{self.BASE_URL}/{config.api_version}"
        self.access_token = config.access_token
        self.form_id = config.form_id
        self.distributor_id = config.distributor_id
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test Meta API connection"""
        try:
            if not self.access_token or not self.form_id:
                return False, "Eksik API bilgileri"
            
            # Test endpoint
            url = f"{self.api_url}/{self.form_id}"
            params = {'access_token': self.access_token}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return True, "Bağlantı başarılı"
            else:
                error_msg = response.json().get('error', {}).get('message', 'Bilinmeyen hata')
                return False, f"API hatası: {error_msg}"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Meta API bağlantı hatası: {str(e)}")
            return False, f"Bağlantı hatası: {str(e)}"
        except Exception as e:
            logger.error(f"Meta API test hatası: {str(e)}")
            return False, f"Test hatası: {str(e)}"
    
    def fetch_leads(self, limit: int = 100) -> Tuple[List[Dict], Optional[str]]:
        """Fetch leads from Meta/Facebook lead form"""
        try:
            if not self.access_token or not self.form_id:
                logger.warning(f"Distributor {self.distributor_id}: Eksik API bilgileri")
                return [], "Eksik API bilgileri"
            
            url = f"{self.api_url}/{self.form_id}/leads"
            params = {
                'access_token': self.access_token,
                'limit': limit,
                'fields': 'id,created_time,field_data'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Bilinmeyen hata')
                logger.error(f"Meta API hatası ({self.distributor_id}): {error_msg}")
                return [], error_msg
            
            leads_data = response.json().get('data', [])
            logger.info(f"Distributor {self.distributor_id}: {len(leads_data)} lead alındı")
            
            return leads_data, None
        
        except requests.exceptions.Timeout:
            error = "API timeout"
            logger.error(f"Meta API timeout ({self.distributor_id}): {error}")
            return [], error
        except requests.exceptions.RequestException as e:
            error = str(e)
            logger.error(f"Meta API request hatası ({self.distributor_id}): {error}")
            return [], error
        except Exception as e:
            error = str(e)
            logger.error(f"Lead fetch hatası ({self.distributor_id}): {error}")
            return [], error
    
    def parse_lead_data(self, lead: Dict) -> Dict:
        """Parse lead data from Meta format"""
        try:
            field_data = lead.get('field_data', [])
            parsed_data = {
                'meta_lead_id': lead.get('id'),
                'lead_created_at': lead.get('created_time'),
                'form_data': {}
            }
            
            # Extract field data
            for field in field_data:
                field_name = field.get('name', '').lower()
                field_value = field.get('values', [])[0] if field.get('values') else None
                
                if not field_value:
                    continue
                
                # Map common fields
                if 'ad' in field_name or 'first' in field_name:
                    parsed_data['first_name'] = field_value
                elif 'soyad' in field_name or 'last' in field_name:
                    parsed_data['last_name'] = field_value
                elif 'email' in field_name:
                    parsed_data['email'] = field_value
                elif 'telefon' in field_name or 'phone' in field_name or 'whatsapp' in field_name:
                    # Clean phone number
                    parsed_data['phone'] = self._clean_phone(field_value)
                else:
                    # Store as custom form data
                    parsed_data['form_data'][field_name] = field_value
            
            return parsed_data
        
        except Exception as e:
            logger.error(f"Lead parse hatası: {str(e)}")
            return {}
    
    def store_leads(self, leads_data: List[Dict]) -> Tuple[int, List[str]]:
        """Store leads in database, avoiding duplicates"""
        stored_count = 0
        errors = []
        
        try:
            for lead_data in leads_data:
                try:
                    parsed = self.parse_lead_data(lead_data)
                    
                    if not parsed.get('meta_lead_id'):
                        errors.append("Meta lead ID bulunamadı")
                        continue
                    
                    # Check if lead already exists
                    existing = FacebookLead.query.filter_by(
                        meta_lead_id=parsed['meta_lead_id']
                    ).first()
                    
                    if existing:
                        logger.info(f"Lead zaten mevcut: {parsed['meta_lead_id']}")
                        continue
                    
                    # Create new lead
                    lead_created_at = None
                    if parsed.get('lead_created_at'):
                        try:
                            lead_created_at = datetime.fromisoformat(
                                parsed['lead_created_at'].replace('Z', '+00:00')
                            )
                        except:
                            pass
                    
                    new_lead = FacebookLead(
                        distributor_id=self.distributor_id,
                        meta_lead_id=parsed.get('meta_lead_id'),
                        first_name=parsed.get('first_name', ''),
                        last_name=parsed.get('last_name', ''),
                        email=parsed.get('email', ''),
                        phone=parsed.get('phone', ''),
                        form_data=parsed.get('form_data', {}),
                        lead_created_at=lead_created_at,
                        status='new'
                    )
                    
                    db.session.add(new_lead)
                    db.session.commit()
                    stored_count += 1
                    logger.info(f"Lead kaydedildi: {new_lead.full_name()}")
                
                except Exception as e:
                    db.session.rollback()
                    error_msg = f"Lead saklama hatası: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return stored_count, errors
        
        except Exception as e:
            logger.error(f"Toplu lead saklama hatası: {str(e)}")
            return stored_count, errors
    
    def sync_leads(self, limit: int = 100) -> Dict:
        """Complete sync process: fetch and store leads"""
        result = {
            'success': False,
            'fetched': 0,
            'stored': 0,
            'errors': [],
            'message': ''
        }
        
        try:
            # Fetch leads
            leads_data, error = self.fetch_leads(limit)
            
            if error:
                result['errors'].append(error)
                result['message'] = error
                return result
            
            result['fetched'] = len(leads_data)
            
            if not leads_data:
                result['message'] = "Yeni lead yok"
                result['success'] = True
                return result
            
            # Store leads
            stored, errors = self.store_leads(leads_data)
            result['stored'] = stored
            result['errors'].extend(errors)
            result['message'] = f"{stored}/{result['fetched']} lead kaydedildi"
            result['success'] = True
            
            # Update config
            self.config.last_fetch_time = datetime.utcnow()
            self.config.last_error = None if not errors else '; '.join(errors[:3])
            db.session.commit()
            
            return result
        
        except Exception as e:
            error_msg = f"Sync hatası: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            result['message'] = error_msg
            
            # Update error in config
            try:
                self.config.last_error = error_msg
                db.session.commit()
            except:
                pass
            
            return result
    
    @staticmethod
    def _clean_phone(phone: str) -> str:
        """Clean phone number"""
        if not phone:
            return ''
        # Remove all non-digit characters except + and spaces
        cleaned = ''.join(c for c in phone if c.isdigit() or c in ['+', ' ', '-'])
        # Remove spaces and dashes, keep only + and digits
        cleaned = ''.join(c for c in cleaned if c.isdigit() or c == '+')
        return cleaned
    
    @staticmethod
    def add_lead_interaction(lead_id: int, user_id: int, interaction_type: str, 
                            description: str = '', result: str = '') -> bool:
        """Add interaction record for a lead"""
        try:
            interaction = LeadInteraction(
                lead_id=lead_id,
                user_id=user_id,
                interaction_type=interaction_type,
                description=description,
                result=result
            )
            db.session.add(interaction)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Interaction kaydı hatası: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def update_lead_status(lead_id: int, new_status: str, user_id: int) -> bool:
        """Update lead status and create interaction record"""
        try:
            lead = FacebookLead.query.get(lead_id)
            if not lead:
                return False
            
            old_status = lead.status
            lead.status = new_status
            lead.updated_at = datetime.utcnow()
            
            # Create interaction record
            interaction = LeadInteraction(
                lead_id=lead_id,
                user_id=user_id,
                interaction_type='status_changed',
                description=f"{old_status} → {new_status}",
                result='success'
            )
            
            db.session.add(interaction)
            db.session.commit()
            logger.info(f"Lead {lead_id} status güncellendi: {old_status} → {new_status}")
            return True
        
        except Exception as e:
            logger.error(f"Status update hatası: {str(e)}")
            db.session.rollback()
            return False
