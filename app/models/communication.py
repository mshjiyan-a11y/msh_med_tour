from datetime import datetime
from app import db

class Message(db.Model):
    """Hasta-Koordinator mesajlasma"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Mesaj bilgileri
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Staff/Coordinator (NULL = Bot)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    is_bot_message = db.Column(db.Boolean, default=False)  # Bot tarafından gönderildi mi?
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=True)
    
    # Mesaj icerigi
    message_type = db.Column(db.String(20), default='text')  # text, image, file, voice
    content = db.Column(db.Text, nullable=False)
    attachment_url = db.Column(db.String(500))

    # Çok dillilik (isteğe bağlı çeviri alanları)
    detected_language = db.Column(db.String(10))  # örn: 'tr', 'en'
    target_language = db.Column(db.String(10))    # çeviri istenirse hedef dil
    translated_content = db.Column(db.Text)       # çeviri metni
    
    # Durum
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Sistem
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İliskiler
    sender = db.relationship('User', backref='sent_messages')
    patient = db.relationship('Patient', backref='messages')
    journey = db.relationship('PatientJourney', backref='messages')
    
    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to Patient {self.patient_id}>'


class CommunicationLog(db.Model):
    """Tum iletisim gecmisi (calls, emails, sms, whatsapp)"""
    __tablename__ = 'communication_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Iletisim bilgileri
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Staff who handled
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=True)
    
    # Iletisim turu
    communication_type = db.Column(db.String(20), nullable=False)  # call, email, sms, whatsapp, chat, video_call
    direction = db.Column(db.String(10), nullable=False)  # inbound, outbound
    
    # Icerik
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    duration_seconds = db.Column(db.Integer)  # For calls
    
    # Durum
    status = db.Column(db.String(20), default='completed')  # completed, missed, failed, pending
    
    # Metadata
    phone_number = db.Column(db.String(20))
    email_address = db.Column(db.String(100))
    recording_url = db.Column(db.String(500))  # For call recordings
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İliskiler
    patient = db.relationship('Patient', backref='communication_logs')
    user = db.relationship('User', backref='communication_logs')
    journey = db.relationship('PatientJourney', backref='communication_logs')
    
    def __repr__(self):
        return f'<CommunicationLog {self.communication_type} - Patient {self.patient_id}>'


class PatientFeedback(db.Model):
    """Hasta geri bildirimleri ve degerlendirmeler"""
    __tablename__ = 'patient_feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Geri bildirim bilgileri
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=True)
    
    # Degerlendirme
    feedback_type = db.Column(db.String(30), default='general')  # general, journey, treatment, staff, facility
    rating = db.Column(db.Integer)  # 1-5 stars
    
    # Kategorik degerlendirmeler
    service_quality = db.Column(db.Integer)  # 1-5
    communication_quality = db.Column(db.Integer)  # 1-5
    facility_cleanliness = db.Column(db.Integer)  # 1-5
    treatment_satisfaction = db.Column(db.Integer)  # 1-5
    value_for_money = db.Column(db.Integer)  # 1-5
    
    # Yorum
    comment = db.Column(db.Text)
    suggestions = db.Column(db.Text)
    
    # Referans
    would_recommend = db.Column(db.Boolean)
    referral_likelihood = db.Column(db.Integer)  # 1-10 NPS score
    
    # Durum
    is_public = db.Column(db.Boolean, default=False)  # Websitede göster
    is_featured = db.Column(db.Boolean, default=False)  # Öne çıkan yorumlar
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    # Yanitlama
    response = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    responded_at = db.Column(db.DateTime)
    
    # Metadata
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İliskiler
    patient = db.relationship('Patient', backref='feedbacks')
    journey = db.relationship('PatientJourney', backref='feedbacks')
    encounter = db.relationship('Encounter', backref='feedbacks')
    responder = db.relationship('User', foreign_keys=[responded_by], backref='feedback_responses')
    
    @property
    def nps_category(self):
        """Net Promoter Score kategorisi"""
        if self.referral_likelihood is None:
            return None
        if self.referral_likelihood >= 9:
            return 'promoter'
        elif self.referral_likelihood >= 7:
            return 'passive'
        else:
            return 'detractor'
    
    def __repr__(self):
        return f'<PatientFeedback {self.id} - Rating: {self.rating}>'


class SupportTicket(db.Model):
    """Destek talepleri ve sorun takibi"""
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Ticket bilgileri
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=True)
    
    # Kategori ve oncelik
    category = db.Column(db.String(50), nullable=False)  # medical, logistics, payment, complaint, inquiry
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    
    # Icerik
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Atama ve durum
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='open')  # open, in_progress, waiting_patient, resolved, closed
    
    # Cozum
    resolution = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # SLA
    due_date = db.Column(db.DateTime)
    first_response_at = db.Column(db.DateTime)
    
    # Tags
    tags = db.Column(db.String(200))  # Comma-separated
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # İliskiler
    patient = db.relationship('Patient', backref='support_tickets')
    journey = db.relationship('PatientJourney', backref='support_tickets')
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tickets')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_tickets')
    
    def __repr__(self):
        return f'<SupportTicket {self.ticket_number} - {self.status}>'


class TicketReply(db.Model):
    """Destek ticket yanitlari"""
    __tablename__ = 'ticket_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    
    # Yanitlayan
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_staff = db.Column(db.Boolean, default=True)
    
    # Icerik
    message = db.Column(db.Text, nullable=False)
    attachments = db.Column(db.Text)  # JSON array of file URLs
    
    # Metadata
    is_internal = db.Column(db.Boolean, default=False)  # Internal note, not visible to patient
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İliskiler
    ticket = db.relationship('SupportTicket', backref='replies')
    user = db.relationship('User', backref='ticket_replies')
    
    def __repr__(self):
        return f'<TicketReply {self.id} for Ticket {self.ticket_id}>'


class ChatSession(db.Model):
    """Canli chat oturumlari"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Session bilgileri
    session_id = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    
    # Katilimcilar
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Assigned agent
    
    # Durum
    status = db.Column(db.String(20), default='waiting')  # waiting, active, ended
    
    # Zaman
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    
    # Metadata
    visitor_ip = db.Column(db.String(50))
    visitor_country = db.Column(db.String(50))
    referrer_url = db.Column(db.String(500))
    
    # Degerlendirildi mi
    rated = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)  # 1-5
    
    # İliskiler
    patient = db.relationship('Patient', backref='chat_sessions')
    agent = db.relationship('User', backref='chat_sessions')
    
    def __repr__(self):
        return f'<ChatSession {self.session_id} - {self.status}>'
