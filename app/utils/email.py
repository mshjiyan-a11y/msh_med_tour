"""
Email notification system for MSH Med Tour
Supports: Lead notifications, appointment reminders, etc.
"""
from flask_mail import Message
from flask import current_app
from threading import Thread
from app import mail

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Email gönderme hatası: {e}")

def send_email(subject, recipients, text_body, html_body=None, attachments=None, sender=None):
    """Send email with optional HTML body and attachments

    attachments: list of tuples (filename, mimetype, data: bytes)
    """
    msg = Message(subject, recipients=recipients, sender=sender or current_app.config.get('MAIL_DEFAULT_SENDER'))
    msg.body = text_body
    if html_body:
        msg.html = html_body
    # Attach files if provided
    if attachments:
        for (filename, mimetype, data) in attachments:
            if filename and data:
                msg.attach(filename=filename, content_type=mimetype or 'application/octet-stream', data=data)
    
    # Send asynchronously
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_new_lead_notification(lead, distributor):
    """Notify distributor about new lead"""
    subject = f"Yeni Lead: {lead.first_name} {lead.last_name}"
    
    text_body = f"""
Yeni bir lead kaydı oluşturuldu:

Ad Soyad: {lead.first_name} {lead.last_name}
Telefon: {lead.phone}
E-posta: {lead.email or '-'}
Kaynak: {lead.source}
İlgilendiği Hizmet: {lead.interested_service or '-'}
Mesaj: {lead.message or '-'}

Lead'i görüntülemek için: {current_app.config.get('BASE_URL', '')}/leads/{lead.id}
    """
    
    html_body = f"""
    <h2>Yeni Lead Bildirimi</h2>
    <p>Yeni bir lead kaydı oluşturuldu:</p>
    <table border="1" cellpadding="5">
        <tr><th>Ad Soyad:</th><td>{lead.first_name} {lead.last_name}</td></tr>
        <tr><th>Telefon:</th><td>{lead.phone}</td></tr>
        <tr><th>E-posta:</th><td>{lead.email or '-'}</td></tr>
        <tr><th>Kaynak:</th><td>{lead.source}</td></tr>
        <tr><th>İlgilendiği Hizmet:</th><td>{lead.interested_service or '-'}</td></tr>
        <tr><th>Mesaj:</th><td>{lead.message or '-'}</td></tr>
    </table>
    <p><a href="{current_app.config.get('BASE_URL', '')}/leads/{lead.id}">Lead'i Görüntüle</a></p>
    """
    
    # Send to distributor email
    if distributor.email:
        send_email(subject, [distributor.email], text_body, html_body)

def send_appointment_reminder(encounter, patient):
    """Send appointment reminder to patient"""
    subject = f"Randevu Hatırlatması - {encounter.distributor.name}"
    
    text_body = f"""
Sayın {patient.first_name} {patient.last_name},

{encounter.date.strftime('%d.%m.%Y %H:%M')} tarihinde randevunuz bulunmaktadır.

Randevu Detayları:
Hastane/Klinik: {encounter.distributor.name}
Tarih: {encounter.date.strftime('%d.%m.%Y %H:%M')}
Telefon: {encounter.distributor.phone}
Adres: {encounter.distributor.address}

İyi günler dileriz.
    """
    
    if patient.email:
        send_email(subject, [patient.email], text_body)


def send_encounter_price_quote(encounter, pdf_bytes):
    """Send price quote PDF to patient via email"""
    patient = encounter.patient
    distributor = encounter.distributor
    if not patient.email:
        raise ValueError('Hasta e-posta adresi bulunamadı')

    subject = f"Fiyat Teklifi - {distributor.name}"
    text_body = f"""
Sayın {patient.first_name} {patient.last_name},

Talep ettiğiniz işlem için hazırlanan fiyat teklifini ekte PDF olarak iletiyoruz.

Kurum: {distributor.name}
Tarih: {encounter.date.strftime('%d.%m.%Y') if encounter.date else encounter.created_at.strftime('%d.%m.%Y')}

Her türlü sorunuz için bizimle iletişime geçebilirsiniz.

Saygılarımızla,
{distributor.name}
"""
    html_body = f"""
    <p>Sayın <strong>{patient.first_name} {patient.last_name}</strong>,</p>
    <p>Talep ettiğiniz işlem için hazırlanan <strong>fiyat teklifini</strong> ekte PDF olarak iletiyoruz.</p>
    <p>
        <strong>Kurum:</strong> {distributor.name}<br>
        <strong>Tarih:</strong> {encounter.date.strftime('%d.%m.%Y') if encounter.date else encounter.created_at.strftime('%d.%m.%Y')}
    </p>
    <p>Her türlü sorunuz için bizimle iletişime geçebilirsiniz.</p>
    <p>Saygılarımızla,<br>{distributor.name}</p>
    """

    filename = f"fiyat_teklifi_muayene_{encounter.id}.pdf"
    attachments = [(filename, 'application/pdf', pdf_bytes)]
    send_email(subject, [patient.email], text_body, html_body, attachments)


def send_hotel_reservation_confirmation(reservation, pdf_bytes):
    """Send hotel reservation confirmation PDF to patient"""
    patient = reservation.patient
    distributor = reservation.distributor
    if not patient.email:
        raise ValueError('Hasta e-posta adresi bulunamadı')

    subject = f"Otel Rezervasyon Onayı - {distributor.name}"
    text_body = f"""
Sayın {patient.first_name} {patient.last_name},

{reservation.hotel_name} için otel rezervasyon onayınız ektedir.
Giriş: {reservation.check_in.strftime('%d.%m.%Y')}  Çıkış: {reservation.check_out.strftime('%d.%m.%Y')}  (Toplam {reservation.nights or 0} gece)
Toplam Tutar: {reservation.total_cost:.2f} €

İyi konaklamalar dileriz.
"""
    html_body = f"""
    <p>Sayın <strong>{patient.first_name} {patient.last_name}</strong>,</p>
    <p><strong>{reservation.hotel_name}</strong> için otel rezervasyon onayınız ektedir.</p>
    <p>
      <strong>Giriş:</strong> {reservation.check_in.strftime('%d.%m.%Y')}<br>
      <strong>Çıkış:</strong> {reservation.check_out.strftime('%d.%m.%Y')}<br>
      <strong>Gece:</strong> {reservation.nights or 0}<br>
      <strong>Toplam:</strong> {reservation.total_cost:.2f} €
    </p>
    <p>İyi konaklamalar dileriz.</p>
    """
    filename = f"otel_rezervasyon_{reservation.id}.pdf"
    attachments = [(filename, 'application/pdf', pdf_bytes)]
    send_email(subject, [patient.email], text_body, html_body, attachments)
