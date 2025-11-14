"""Lead scoring system - automatically evaluate lead quality"""

from datetime import datetime, timedelta
from app import db
from app.models.meta_lead import FacebookLead
import logging

logger = logging.getLogger(__name__)


class LeadScoringEngine:
    """Calculate lead score based on multiple factors"""
    
    # Score multipliers
    FACTORS = {
        'contact_complete': 30,      # Has both email and phone
        'quick_response': 20,        # Lead within last 24 hours
        'service_indicated': 25,     # Selected service in form
        'engagement': 15,            # Multiple form fields filled
        'age': 10,                   # Recently created
    }
    
    TOTAL_MAX_SCORE = sum(FACTORS.values())  # 100
    
    @staticmethod
    def calculate_score(lead: FacebookLead) -> int:
        """Calculate lead quality score (0-100)"""
        score = 0
        
        # Factor 1: Contact information completeness
        if lead.email and lead.phone:
            score += LeadScoringEngine.FACTORS['contact_complete']
        elif lead.email or lead.phone:
            score += LeadScoringEngine.FACTORS['contact_complete'] // 2
        
        # Factor 2: How recent the lead is
        age_hours = (datetime.utcnow() - lead.created_at).total_seconds() / 3600
        if age_hours < 1:
            score += LeadScoringEngine.FACTORS['age']
        elif age_hours < 24:
            score += LeadScoringEngine.FACTORS['age'] // 2
        
        # Factor 3: Quick response (lead created within 24h)
        if lead.lead_created_at:
            lead_age = (datetime.utcnow() - lead.lead_created_at).total_seconds() / 3600
            if lead_age < 24:
                score += LeadScoringEngine.FACTORS['quick_response']
        
        # Factor 4: Service interest indicated
        form_data = lead.form_data or {}
        service_fields = ['interested_service', 'service', 'procedure', 'treatment']
        if any(form_data.get(f) for f in service_fields):
            score += LeadScoringEngine.FACTORS['service_indicated']
        
        # Factor 5: Form completeness (engagement)
        filled_fields = sum(1 for v in (form_data or {}).values() if v)
        if filled_fields >= 3:
            score += LeadScoringEngine.FACTORS['engagement']
        elif filled_fields >= 1:
            score += LeadScoringEngine.FACTORS['engagement'] // 2
        
        return min(score, LeadScoringEngine.TOTAL_MAX_SCORE)
    
    @staticmethod
    def get_score_level(score: int) -> str:
        """Get score level label"""
        if score >= 80:
            return 'excellent'  # Çok İyi
        elif score >= 60:
            return 'good'        # İyi
        elif score >= 40:
            return 'medium'      # Orta
        elif score >= 20:
            return 'low'         # Düşük
        else:
            return 'very_low'    # Çok Düşük
    
    @staticmethod
    def get_score_color(score: int) -> str:
        """Get badge color for score"""
        level = LeadScoringEngine.get_score_level(score)
        colors = {
            'excellent': 'success',   # Green
            'good': 'info',           # Blue
            'medium': 'warning',      # Yellow
            'low': 'orange',          # Orange
            'very_low': 'danger'      # Red
        }
        return colors.get(level, 'secondary')
    
    @staticmethod
    def batch_score_leads(leads=None):
        """Calculate scores for all leads or specified ones"""
        if leads is None:
            leads = FacebookLead.query.all()
        
        scores = {}
        for lead in leads:
            score = LeadScoringEngine.calculate_score(lead)
            scores[lead.id] = {
                'score': score,
                'level': LeadScoringEngine.get_score_level(score),
                'color': LeadScoringEngine.get_score_color(score)
            }
        
        return scores
    
    @staticmethod
    def get_top_leads(limit=10, min_score=50):
        """Get top scoring leads"""
        all_leads = FacebookLead.query.all()
        
        scored_leads = [
            (lead, LeadScoringEngine.calculate_score(lead))
            for lead in all_leads
            if LeadScoringEngine.calculate_score(lead) >= min_score
        ]
        
        # Sort by score descending
        scored_leads.sort(key=lambda x: x[1], reverse=True)
        
        return scored_leads[:limit]
    
    @staticmethod
    def get_priority_recommendations():
        """Get lead management recommendations based on scoring"""
        recommendations = {
            'high_quality_unassigned': [],
            'low_quality_contacted': [],
            'abandoned_high_quality': [],
        }
        
        all_leads = FacebookLead.query.all()
        
        for lead in all_leads:
            score = LeadScoringEngine.calculate_score(lead)
            
            # High quality leads that haven't been assigned
            if score >= 70 and lead.status == 'new':
                recommendations['high_quality_unassigned'].append({
                    'lead_id': lead.id,
                    'name': lead.full_name(),
                    'score': score,
                    'reason': 'Yüksek kaliteli lead henüz işleme alınmamış'
                })
            
            # Low quality leads that have been contacted
            if score <= 30 and lead.status == 'contacted':
                recommendations['low_quality_contacted'].append({
                    'lead_id': lead.id,
                    'name': lead.full_name(),
                    'score': score,
                    'reason': 'Düşük kaliteli lead - işlem durdurulabilir'
                })
            
            # High quality leads not contacted in 48 hours
            if score >= 60 and lead.status == 'assigned':
                age_hours = (datetime.utcnow() - lead.created_at).total_seconds() / 3600
                if age_hours > 48:
                    recommendations['abandoned_high_quality'].append({
                        'lead_id': lead.id,
                        'name': lead.full_name(),
                        'score': score,
                        'age_hours': int(age_hours),
                        'reason': 'Yüksek kaliteli lead 48 saattir işleme alınmadı'
                    })
        
        return recommendations


def add_score_to_lead(lead_id):
    """Utility function to add score to a lead in template"""
    lead = FacebookLead.query.get(lead_id)
    if lead:
        score = LeadScoringEngine.calculate_score(lead)
        return {
            'score': score,
            'level': LeadScoringEngine.get_score_level(score),
            'color': LeadScoringEngine.get_score_color(score),
            'percentage': f"{(score / 100 * 100):.0f}%"
        }
    return None
