"""Advanced analytics and conversion funnel tracking"""

from datetime import datetime, timedelta
from app import db
from app.models.meta_lead import FacebookLead, LeadInteraction
import json


class LeadAnalytics:
    """Analyze lead data and track conversion funnels"""
    
    @staticmethod
    def get_conversion_funnel(days=30):
        """Calculate conversion funnel for last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        leads = FacebookLead.query.filter(FacebookLead.created_at >= start_date).all()
        
        # Count by status
        statuses = {
            'total': len(leads),
            'new': len([l for l in leads if l.status == 'new']),
            'assigned': len([l for l in leads if l.status == 'assigned']),
            'contacted': len([l for l in leads if l.status == 'contacted']),
            'converted': len([l for l in leads if l.status == 'converted']),
            'rejected': len([l for l in leads if l.status == 'rejected']),
        }
        
        # Calculate conversion rates
        conversion_rates = {}
        if statuses['total'] > 0:
            conversion_rates = {
                'to_assigned': round((statuses['assigned'] / statuses['total']) * 100, 2),
                'to_contacted': round((statuses['contacted'] / statuses['total']) * 100, 2),
                'to_converted': round((statuses['converted'] / statuses['total']) * 100, 2),
                'rejection_rate': round((statuses['rejected'] / statuses['total']) * 100, 2),
            }
        
        return {
            'statuses': statuses,
            'rates': conversion_rates,
            'period_days': days
        }
    
    @staticmethod
    def get_daily_stats(days=30):
        """Get daily lead statistics for the last N days"""
        daily_stats = {}
        
        for i in range(days, 0, -1):
            date = datetime.utcnow() - timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            
            # Get leads created on this day
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_leads = FacebookLead.query.filter(
                FacebookLead.created_at.between(start, end)
            ).all()
            
            daily_stats[date_key] = {
                'total': len(day_leads),
                'new': len([l for l in day_leads if l.status == 'new']),
                'converted': len([l for l in day_leads if l.status == 'converted']),
                'conversion_rate': round(
                    (len([l for l in day_leads if l.status == 'converted']) / len(day_leads) * 100)
                    if day_leads else 0, 2
                )
            }
        
        return daily_stats
    
    @staticmethod
    def get_source_analysis():
        """Analyze leads by source (Facebook form, distributor, etc)"""
        all_leads = FacebookLead.query.all()
        
        by_distributor = {}
        for lead in all_leads:
            dist_name = lead.distributor.name
            if dist_name not in by_distributor:
                by_distributor[dist_name] = {
                    'total': 0,
                    'new': 0,
                    'contacted': 0,
                    'converted': 0,
                    'conversion_rate': 0
                }
            
            by_distributor[dist_name]['total'] += 1
            if lead.status == 'new':
                by_distributor[dist_name]['new'] += 1
            elif lead.status == 'contacted':
                by_distributor[dist_name]['contacted'] += 1
            elif lead.status == 'converted':
                by_distributor[dist_name]['converted'] += 1
        
        # Calculate rates
        for dist in by_distributor.values():
            if dist['total'] > 0:
                dist['conversion_rate'] = round((dist['converted'] / dist['total']) * 100, 2)
        
        return by_distributor
    
    @staticmethod
    def get_assignment_analytics():
        """Analyze which staff members are most effective"""
        all_leads = FacebookLead.query.filter(FacebookLead.assigned_to_id.isnot(None)).all()
        
        by_user = {}
        for lead in all_leads:
            user_name = lead.assigned_to.username if lead.assigned_to else 'Unassigned'
            if user_name not in by_user:
                by_user[user_name] = {
                    'assigned_count': 0,
                    'contacted': 0,
                    'converted': 0,
                    'conversion_rate': 0,
                    'avg_response_time': 0
                }
            
            by_user[user_name]['assigned_count'] += 1
            if lead.status == 'contacted':
                by_user[user_name]['contacted'] += 1
            if lead.status == 'converted':
                by_user[user_name]['converted'] += 1
        
        # Calculate rates
        for user in by_user.values():
            if user['assigned_count'] > 0:
                user['conversion_rate'] = round(
                    (user['converted'] / user['assigned_count']) * 100, 2
                )
        
        return by_user
    
    @staticmethod
    def get_interaction_stats():
        """Get interaction type statistics"""
        all_interactions = LeadInteraction.query.all()
        
        interaction_types = {}
        for interaction in all_interactions:
            itype = interaction.interaction_type
            if itype not in interaction_types:
                interaction_types[itype] = {
                    'count': 0,
                    'success': 0,
                    'failed': 0
                }
            
            interaction_types[itype]['count'] += 1
            if interaction.result == 'success':
                interaction_types[itype]['success'] += 1
            else:
                interaction_types[itype]['failed'] += 1
        
        return interaction_types
    
    @staticmethod
    def get_response_time_stats():
        """Calculate average response time (time to first contact)"""
        leads_with_interactions = FacebookLead.query.filter(
            FacebookLead.id.in_(
                db.session.query(LeadInteraction.lead_id).distinct()
            )
        ).all()
        
        response_times = []
        for lead in leads_with_interactions:
            # Get first interaction
            first_interaction = LeadInteraction.query.filter_by(
                lead_id=lead.id
            ).order_by(LeadInteraction.created_at.asc()).first()
            
            if first_interaction:
                response_time = (first_interaction.created_at - lead.created_at).total_seconds() / 3600
                response_times.append(response_time)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            return {
                'average_hours': round(avg_response_time, 2),
                'min_hours': round(min_response_time, 2),
                'max_hours': round(max_response_time, 2),
                'sample_size': len(response_times)
            }
        
        return {
            'average_hours': 0,
            'min_hours': 0,
            'max_hours': 0,
            'sample_size': 0
        }
    
    @staticmethod
    def generate_report(report_type='monthly'):
        """Generate comprehensive report"""
        if report_type == 'daily':
            days = 1
        elif report_type == 'weekly':
            days = 7
        elif report_type == 'monthly':
            days = 30
        else:
            days = 30
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period': report_type,
            'days': days,
            'funnel': LeadAnalytics.get_conversion_funnel(days),
            'daily_stats': LeadAnalytics.get_daily_stats(days),
            'by_distributor': LeadAnalytics.get_source_analysis(),
            'by_user': LeadAnalytics.get_assignment_analytics(),
            'interactions': LeadAnalytics.get_interaction_stats(),
            'response_time': LeadAnalytics.get_response_time_stats(),
        }
        
        return report
    
    @staticmethod
    def export_report_json(report_type='monthly'):
        """Export report as JSON"""
        report = LeadAnalytics.generate_report(report_type)
        return json.dumps(report, ensure_ascii=False, indent=2, default=str)
    
    @staticmethod
    def export_report_html(report_type='monthly'):
        """Generate HTML report"""
        report = LeadAnalytics.generate_report(report_type)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="tr" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>Lead Analytics Report - {report_type.upper()}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
                th {{ background-color: #f5f5f5; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Lead Analytics Report ({report_type.upper()})</h1>
            <p>Generated: {report['generated_at']}</p>
            
            <h2>Conversion Funnel</h2>
            <div class="metric">
                <strong>Total Leads:</strong> {report['funnel']['statuses']['total']}
            </div>
            <div class="metric">
                <strong>Converted:</strong> {report['funnel']['statuses']['converted']}
            </div>
            <div class="metric">
                <strong>Conversion Rate:</strong> {report['funnel']['rates'].get('to_converted', 0)}%
            </div>
            
            <h2>By Distributor</h2>
            <table>
                <thead>
                    <tr>
                        <th>Distributor</th>
                        <th>Total</th>
                        <th>Converted</th>
                        <th>Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'<tr><td>{k}</td><td>{v["total"]}</td><td>{v["converted"]}</td><td>{v["conversion_rate"]}%</td></tr>' for k, v in report['by_distributor'].items())}
                </tbody>
            </table>
            
            <h2>Response Time Stats</h2>
            <div class="metric">
                <strong>Average Response Time:</strong> {report['response_time']['average_hours']} hours
            </div>
        </body>
        </html>
        """
        
        return html
