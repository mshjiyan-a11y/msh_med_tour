"""
Currency Rate Management
Döviz kuru yönetimi - otomatik güncellemeler ve çoklu para birimi desteği
"""
from datetime import datetime
from app import db


class CurrencyRate(db.Model):
    """Döviz kurları tablosu"""
    __tablename__ = 'currency_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Para birimi bilgileri
    base_currency = db.Column(db.String(3), nullable=False, default='USD')  # Base currency (USD, EUR, TRY)
    target_currency = db.Column(db.String(3), nullable=False)  # Target currency
    rate = db.Column(db.Float, nullable=False)  # Conversion rate (1 base = X target)
    
    # Güncelleme bilgileri
    source = db.Column(db.String(50))  # API source: 'exchangerate-api', 'tcmb', 'manual'
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    is_manual = db.Column(db.Boolean, default=False)  # Manuel mi otomatik mi?
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    distributor = db.relationship('Distributor', backref='currency_rates')
    
    # Unique constraint: one rate per base-target pair per distributor
    __table_args__ = (
        db.UniqueConstraint('distributor_id', 'base_currency', 'target_currency', name='_currency_pair_uc'),
    )
    
    def __repr__(self):
        return f'<CurrencyRate {self.base_currency}/{self.target_currency} = {self.rate}>'
    
    @staticmethod
    def get_rate(distributor_id, from_currency, to_currency):
        """
        Döviz kuru al (çapraz kur hesaplamasıyla)
        
        Args:
            distributor_id: Distributor ID
            from_currency: Kaynak para birimi
            to_currency: Hedef para birimi
            
        Returns:
            float: Conversion rate veya None
        """
        if from_currency == to_currency:
            return 1.0
        
        # Direct rate lookup
        direct = CurrencyRate.query.filter_by(
            distributor_id=distributor_id,
            base_currency=from_currency,
            target_currency=to_currency
        ).first()
        
        if direct:
            return direct.rate
        
        # Reverse rate lookup
        reverse = CurrencyRate.query.filter_by(
            distributor_id=distributor_id,
            base_currency=to_currency,
            target_currency=from_currency
        ).first()
        
        if reverse and reverse.rate != 0:
            return 1.0 / reverse.rate
        
        # Cross-rate calculation via base currency (e.g., TRY->EUR via USD)
        # Get base currency from settings
        from app.models.settings import AppSettings
        settings = AppSettings.get(distributor_id)
        base = getattr(settings, 'base_currency', 'USD')
        
        if from_currency != base and to_currency != base:
            # from_currency -> base
            from_to_base = CurrencyRate.get_rate(distributor_id, from_currency, base)
            # base -> to_currency
            base_to_to = CurrencyRate.get_rate(distributor_id, base, to_currency)
            
            if from_to_base and base_to_to:
                return from_to_base * base_to_to
        
        return None
    
    @staticmethod
    def convert(amount, from_currency, to_currency, distributor_id):
        """
        Para birimi dönüştürme
        
        Args:
            amount: Miktar
            from_currency: Kaynak para birimi
            to_currency: Hedef para birimi
            distributor_id: Distributor ID
            
        Returns:
            float: Dönüştürülmüş miktar veya None
        """
        if not amount:
            return None
        
        rate = CurrencyRate.get_rate(distributor_id, from_currency, to_currency)
        if rate:
            return round(amount * rate, 2)
        
        return None


class PriceListItem(db.Model):
    """Fiyat listesi - katalog için"""
    __tablename__ = 'price_list_items'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Hizmet bilgileri
    category = db.Column(db.String(50), nullable=False)  # hair, dental, eye, aesthetic, bariatric, ivf, checkup
    service_code = db.Column(db.String(50), nullable=False)  # Unique service code
    service_name_tr = db.Column(db.String(200), nullable=False)
    service_name_en = db.Column(db.String(200))
    service_name_ar = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Fiyatlandırma (base currency)
    base_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Görünürlük ve sıralama
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    distributor = db.relationship('Distributor', backref='price_list_items')
    
    def __repr__(self):
        return f'<PriceListItem {self.service_code} - {self.service_name_tr}>'
    
    def get_price_in_currency(self, target_currency):
        """Belirli bir para biriminde fiyat al"""
        if self.currency == target_currency:
            return self.base_price
        
        converted = CurrencyRate.convert(
            self.base_price,
            self.currency,
            target_currency,
            self.distributor_id
        )
        return converted if converted else self.base_price
