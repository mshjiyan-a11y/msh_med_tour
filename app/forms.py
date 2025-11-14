from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, DateField, SelectField,
    BooleanField, FloatField, DateTimeField
)
from wtforms.validators import DataRequired, Email, Optional, Length


class PatientForm(FlaskForm):
    first_name = StringField('Ad', validators=[DataRequired(message='Ad alanı zorunludur')])
    last_name = StringField('Soyad', validators=[DataRequired(message='Soyad alanı zorunludur')])
    email = StringField('E-posta', validators=[Optional(), Email(message='Geçerli bir e-posta adresi giriniz')])
    phone = StringField('Telefon', validators=[DataRequired(message='Telefon alanı zorunludur')])
    dob = DateField('Doğum Tarihi', validators=[Optional()])
    nationality = StringField('Uyruk', validators=[Optional()])
    passport_number = StringField('Pasaport No', validators=[Optional()])
    notes = TextAreaField('Notlar', validators=[Optional(), Length(max=1000, message='Notlar 1000 karakterden uzun olamaz')])


class DistributorForm(FlaskForm):
    name = StringField('Hastane/Klinik Adı', validators=[DataRequired(message='Ad alanı zorunludur')])
    contact_name = StringField('İletişim Kişisi', validators=[Optional()])
    email = StringField('E-posta', validators=[DataRequired(), Email(message='Geçerli bir e-posta adresi giriniz')])
    phone = StringField('Telefon', validators=[Optional()])
    whatsapp = StringField('WhatsApp', validators=[Optional()])
    address = TextAreaField('Adres', validators=[Optional()])
    city = StringField('Şehir', validators=[Optional()])
    country = StringField('Ülke', validators=[Optional()])

    # Web & Social Media
    website = StringField('Website', validators=[Optional()])
    facebook = StringField('Facebook', validators=[Optional()])
    instagram = StringField('Instagram', validators=[Optional()])
    twitter = StringField('Twitter', validators=[Optional()])
    linkedin = StringField('LinkedIn', validators=[Optional()])

    # Legal & Branding
    hospital_license = StringField('Hastane Ruhsat No', validators=[Optional()])
    tax_number = StringField('Vergi No', validators=[Optional()])
    color_hex = StringField('Marka Rengi', validators=[Optional()], default='#7a001d')
    logo = FileField('Logo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Sadece resim dosyaları!')])
    pdf_footer_text = TextAreaField('PDF Alt Yazı', validators=[Optional()])

    # Module Enablement
    enable_hair = BooleanField('Saç Ekimi Modülü', default=False)
    enable_teeth = BooleanField('Diş Modülü', default=False)
    enable_eye = BooleanField('Göz Modülü', default=False)

    # Pricing Configuration
    price_per_graft = FloatField('Greft Başı Fiyat', validators=[Optional()], default=0)
    currency = SelectField(
        'Para Birimi',
        choices=[('EUR', 'EUR - €'), ('USD', 'USD - $'), ('TRY', 'TRY - ₺'), ('GBP', 'GBP - £')],
        default='EUR'
    )

    is_active = BooleanField('Aktif', default=True)


class HotelReservationForm(FlaskForm):
    # Hotel Information
    hotel_name = StringField('Otel Adı', validators=[DataRequired(message='Otel adı zorunludur')])
    hotel_address = TextAreaField('Otel Adresi', validators=[Optional()])
    hotel_phone = StringField('Otel Telefon', validators=[Optional()])
    hotel_stars = SelectField(
        'Yıldız',
        choices=[(None, 'Seçiniz'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        coerce=lambda x: int(x) if x not in (None, '', 'None') else None,
        validators=[Optional()]
    )
    room_type = SelectField(
        'Oda Tipi',
        choices=[('single', 'Tek Kişilik'), ('double', 'Çift Kişilik'), ('suite', 'Suit'), ('deluxe', 'Deluxe')],
        validators=[Optional()]
    )

    # Dates
    check_in = DateField('Giriş Tarihi', validators=[DataRequired(message='Giriş tarihi zorunludur')])
    check_out = DateField('Çıkış Tarihi', validators=[DataRequired(message='Çıkış tarihi zorunludur')])

    # Pricing
    price_per_night = FloatField('Gecelik Fiyat (€)', validators=[Optional()], default=0)

    currency = SelectField(
        'Para Birimi',
        choices=[('EUR', 'EUR (€)'), ('USD', 'USD ($)'), ('TRY', 'TRY (₺)'), ('GBP', 'GBP (£)')],
        default='EUR',
        validators=[Optional()]
    )

    # Transfer
    transfer_included = BooleanField('Transfer Dahil', default=False)
    transfer_type = SelectField(
        'Transfer Tipi',
        choices=[('airport_pickup', 'Havaalanı Karşılama'), ('round_trip', 'Gidiş-Dönüş'), ('one_way', 'Tek Yön')],
        validators=[Optional()]
    )
    transfer_cost = FloatField('Transfer Ücreti (€)', validators=[Optional()], default=0)

    # Airport
    airport_code = StringField('Havaalanı Kodu', validators=[Optional()])
    airport_name = StringField('Havaalanı Adı', validators=[Optional()])
    flight_number = StringField('Uçuş Numarası', validators=[Optional()])
    arrival_time = DateTimeField('Varış Saati', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    departure_time = DateTimeField('Kalkış Saati', format='%Y-%m-%dT%H:%M', validators=[Optional()])

    # Additional
    breakfast_included = BooleanField('Kahvaltı Dahil', default=True)
    wifi_included = BooleanField('WiFi Dahil', default=True)

    # Status
    status = SelectField('Durum', choices=[('pending', 'Bekliyor'), ('confirmed', 'Onaylandı'), ('cancelled', 'İptal')], default='pending')
    confirmation_number = StringField('Onay Numarası', validators=[Optional()])

    # Notes
    notes = TextAreaField('Notlar', validators=[Optional()])
    special_requests = TextAreaField('Özel İstekler', validators=[Optional()])
