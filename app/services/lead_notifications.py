"""Email notifications for lead events"""

from flask_mail import Message
from app import mail
from app.models.meta_lead import FacebookLead
from app.models.user import User
import logging
from threading import Thread

logger = logging.getLogger(__name__)


class LeadEmailNotifications:
    """Handle email notifications for lead events"""
    
    @staticmethod
    def send_async(app, msg):
        """Send email asynchronously"""
        with app.app_context():
            try:
                mail.send(msg)
                logger.info(f"Email sent to {msg.recipients}")
            except Exception as e:
                logger.error(f"Email send failed: {str(e)}")
    
    @staticmethod
    def notify_new_lead(lead: FacebookLead):
        """Notify admin about new high-quality lead"""
        from app import create_app
        
        app = create_app()
        
        # Get admin users
        admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).all()
        
        if not admins:
            return
        
        from app.services.lead_scoring import LeadScoringEngine
        score = LeadScoringEngine.calculate_score(lead)
        
        # Only notify for decent quality leads
        if score < 30:
            return
        
        for admin in admins:
            if not admin.email:
                continue
            
            subject = f"Yeni Lead: {lead.full_name()} (Skor: {score})"
            
            html = f"""
            <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <h2>Yeni Lead Alındı!</h2>
                
                <p><strong>Ad Soyad:</strong> {lead.full_name()}</p>
                <p><strong>Email:</strong> {lead.email or '-'}</p>
                <p><strong>Telefon:</strong> {lead.phone or '-'}</p>
                <p><strong>Dağıtıcı:</strong> {lead.distributor.name}</p>
                
                <p><strong>Lead Kalitesi Skoru:</strong> 
                    <span style="background-color: 
                        {'#28a745' if score >= 80 else
                         '#17a2b8' if score >= 60 else
                         '#ffc107' if score >= 40 else '#dc3545'};
                        color: white; padding: 5px 10px; border-radius: 3px;">
                        {score}/100
                    </span>
                </p>
                
                <h3>Form Bilgileri:</h3>
                <ul>
                    {''.join(f'<li>{k}: {v}</li>' for k, v in (lead.form_data or {}).items())}
                </ul>
                
                <p style="margin-top: 20px;">
                    <a href="http://localhost:5000/admin/facebook-leads/{lead.id}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Lead'i Görüntüle
                    </a>
                </p>
                
                <hr />
                <p style="color: #666; font-size: 12px;">
                    Bu email otomatik olarak gönderilmiştir. Lütfen cevap vermeyin.
                </p>
            </div>
            """
            
            msg = Message(
                subject=subject,
                recipients=[admin.email],
                html=html
            )
            
            # Send in background thread
            Thread(target=LeadEmailNotifications.send_async, args=(app, msg)).start()
            logger.info(f"New lead notification sent to {admin.email}")
    
    @staticmethod
    def notify_status_change(lead: FacebookLead, old_status: str, new_status: str, changed_by: User):
        """Notify assigned user about status change"""
        from app import create_app
        
        app = create_app()
        
        # Only notify if lead is assigned
        if not lead.assigned_to or not lead.assigned_to.email:
            return
        
        subject = f"Lead Durumu Güncellendi: {lead.full_name()} ({old_status} → {new_status})"
        
        html = f"""
        <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
            <h2>Lead Durumu Değiştirildi</h2>
            
            <p>Merhaba <strong>{lead.assigned_to.username}</strong>,</p>
            
            <p>Sizinle ilişkili olan aşağıdaki lead'in durumu güncellenmiştir:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                <p><strong>Lead:</strong> {lead.full_name()}</p>
                <p><strong>Email:</strong> {lead.email}</p>
                <p><strong>Eski Durum:</strong> <span style="color: #999;">{old_status}</span></p>
                <p><strong>Yeni Durum:</strong> <span style="color: #0066cc; font-weight: bold;">{new_status}</span></p>
                <p><strong>Değiştirenler:</strong> {changed_by.username}</p>
            </div>
            
            <p style="margin-top: 20px;">
                <a href="http://localhost:5000/admin/facebook-leads/{lead.id}" 
                   style="background-color: #007bff; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Lead Detaylarını Görüntüle
                </a>
            </p>
            
            <hr />
            <p style="color: #666; font-size: 12px;">
                Bu email otomatik olarak gönderilmiştir. Lütfen cevap vermeyin.
            </p>
        </div>
        """
        
        msg = Message(
            subject=subject,
            recipients=[lead.assigned_to.email],
            html=html
        )
        
        Thread(target=LeadEmailNotifications.send_async, args=(app, msg)).start()
        logger.info(f"Status change notification sent to {lead.assigned_to.email}")
    
    @staticmethod
    def send_daily_summary(distributor_id):
        """Send daily summary email to distributors"""
        from app import create_app
        from app.models import Distributor
        from app.services.lead_scoring import LeadScoringEngine
        
        app = create_app()
        
        with app.app_context():
            distributor = Distributor.query.get(distributor_id)
            if not distributor:
                return
            
            # Get summary stats
            leads = FacebookLead.query.filter_by(distributor_id=distributor_id).all()
            
            if not leads:
                return
            
            new_leads = [l for l in leads if l.status == 'new']
            contacted = [l for l in leads if l.status == 'contacted']
            converted = [l for l in leads if l.status == 'converted']
            
            # Get top scoring leads
            top_leads = LeadScoringEngine.get_top_leads(limit=5)
            
            # Send to admin
            admin = User.query.filter_by(distributor_id=distributor_id).filter(
                User.role.in_(['admin', 'superadmin'])
            ).first()
            
            if not admin or not admin.email:
                return
            
            subject = f"Günlük Lead Özeti - {distributor.name}"
            
            html = f"""
            <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <h2>Günlük Lead Özeti</h2>
                <p><strong>Tarih:</strong> {datetime.now().strftime('%d.%m.%Y')}</p>
                <p><strong>Dağıtıcı:</strong> {distributor.name}</p>
                
                <h3>İstatistikler:</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Toplam Lead</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;"><strong>{len(leads)}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Yeni</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{len(new_leads)}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;">İletişim Kuruldu</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{len(contacted)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Dönüştürülmüş</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{len(converted)}</td>
                    </tr>
                </table>
                
                <h3 style="margin-top: 20px;">En İyi Lead'ler:</h3>
                <ol style="direction: ltr; text-align: left;">
                    {''.join(f'<li>{lead.full_name()} ({score}/100)</li>' for lead, score in top_leads)}
                </ol>
                
                <hr />
                <p style="color: #666; font-size: 12px;">
                    Bu email otomatik olarak gönderilmiştir. Lütfen cevap vermeyin.
                </p>
            </div>
            """
            
            msg = Message(
                subject=subject,
                recipients=[admin.email],
                html=html
            )
            
            Thread(target=LeadEmailNotifications.send_async, args=(app, msg)).start()
            logger.info(f"Daily summary sent to {admin.email}")


from datetime import datetime
