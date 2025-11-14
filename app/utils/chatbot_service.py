"""
Chatbot Service - Basit kural tabanlı otomatik yanıtlayıcı
Gelecekte ML/NLP modelleri veya embedding-tabanlı semantik arama eklenebilir
"""
import re
from typing import Optional, Tuple, Dict
import logging
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)

# Anahtar kelime - yanıt eşleştirmeleri (çok dilli)
KEYWORD_RESPONSES = {
    # Türkçe
    'randevu': 'Randevu için size yardımcı olabilirim. Hangi tarih ve saat aralığı sizin için uygun?',
    'ücret': 'Tedavi ücretlerimiz hakkında detaylı bilgi için lütfen koordinatörümüzle görüşün. Hemen size ulaşacaklar.',
    'fiyat': 'Fiyat bilgisi için size özel teklif hazırlayacağız. Koordinatörümüz en kısa sürede iletişime geçecek.',
    'otel': 'Otel rezervasyonlarınız için size destek sağlıyoruz. Hangi tarihler için konaklama düşünüyorsunuz?',
    'transfer': 'Havaalanı transfer hizmetimiz mevcuttur. Varış bilgilerinizi paylaşırsanız transferinizi ayarlayabiliriz.',
    'vize': 'Vize işlemleri için size rehberlik edebiliriz. Hangi ülke vatandaşısınız?',
    'whatsapp': 'WhatsApp üzerinden de bize ulaşabilirsiniz: +90 XXX XXX XX XX',
    'çalışma saatleri': 'Hafta içi 09:00-18:00 saatleri arasında hizmetinizdeyiz.',
    'acil': '⚠️ Acil durumlar için lütfen +90 XXX XXX XX XX numarasını arayın.',
    
    # İngilizce
    'appointment': 'I can help you with an appointment. What date and time works best for you?',
    'price': 'For detailed pricing information, our coordinator will contact you shortly.',
    'cost': 'We will prepare a personalized quote for you. Our coordinator will reach out soon.',
    'hotel': 'We can assist with hotel reservations. What dates are you considering?',
    'transfer': 'Airport transfer service is available. Please share your arrival details.',
    'visa': 'We can guide you through the visa process. What is your nationality?',
    'working hours': 'We are available Monday-Friday, 09:00-18:00.',
    'emergency': '⚠️ For emergencies, please call +90 XXX XXX XX XX',
    
    # Arapça
    'موعد': 'يمكنني مساعدتك في حجز موعد. ما هو التاريخ والوقت المناسب لك؟',
    'سعر': 'للحصول على معلومات تفصيلية عن الأسعار، سيتواصل معك منسقنا قريباً.',
    'فندق': 'يمكننا المساعدة في حجز الفندق. ما هي التواريخ التي تفكر فيها؟',
}

# Genel/fallback yanıtlar
FALLBACK_RESPONSES = [
    'Size nasıl yardımcı olabilirim? Koordinatörümüz en kısa sürede size dönüş yapacak.',
    'Sorunuzla ilgileniyoruz. Uzman ekibimiz kısa süre içinde yanıt verecek.',
    'Mesajınız alındı. Destek ekibimiz en kısa sürede size ulaşacak.',
]

# FAQ sorular - cevaplar (TR + EN + AR)
FAQ_PATTERNS = {
    # Türkçe
    r'ne zaman (açık|çalış|kapan)': 'Hafta içi 09:00-18:00 saatleri arasında hizmetinizdeyiz. Hafta sonları kapalıyız.',
    r'(kaç gün|ne kadar süre|tedavi süresi)': 'Tedavi süreniz durumunuza göre değişmektedir. Koordinatörümüz size özel plan hazırlayacak.',
    r'(hangi dil|dil desteği|tercüman)': 'Türkçe, İngilizce ve Arapça dillerinde hizmet veriyoruz. İhtiyacınıza göre tercüman desteği sağlanabilir.',
    r'(ödeme|taksit|kredi kartı)': 'Nakit, kredi kartı ve banka havalesi ile ödeme kabul edilmektedir. Taksit seçenekleri için koordinatörünüzle görüşün.',

    # English
    r'(when .*open|opening hours|business hours)': 'We are available Monday-Friday, 09:00-18:00 (UTC+3). Closed on weekends.',
    r'(how long .*treatment|treatment duration|how many days .*treatment)': 'Treatment duration varies by individual case. Our coordinator will prepare a personalized plan for you.',
    r'(language support|interprete?r|translator)': 'We provide support in Turkish, English, and Arabic. Interpreter service can be arranged if needed.',
    r'(payment methods|how .*pay|installments?|credit card)': 'We accept cash, credit card, and bank transfer. Ask your coordinator for available installment options.',

    # Arabic
    r'(متى تفتح|ساعات العمل|اوقات الدوام)': 'نحن متاحون من الإثنين إلى الجمعة، 09:00-18:00 (UTC+3). مغلقون في عطلة نهاية الأسبوع.',
    r'(مدة العلاج|كم يوم يستغرق العلاج)': 'مدة العلاج تختلف حسب حالتك الفردية. سيقوم منسقنا بإعداد خطة مخصصة لك.',
    r'(دعم لغوي|مترجم|لغة)': 'نوفر الدعم باللغات التركية والإنجليزية والعربية. يمكن ترتيب مترجم عند الحاجة.',
    r'(طرق الدفع|كيف ادفع|اقساط|بطاقة|كريدت)': 'نقبل الدفع نقداً وبطاقة الائتمان والتحويل البنكي. اسأل منسقك عن خيارات التقسيط المتاحة.',
}

# Bot yanıt frekans sınırlaması (in-memory; production'da kalıcı store önerilir)
_LAST_RESPONSE: Dict[int, datetime] = {}
_MIN_INTERVAL = timedelta(seconds=30)  # Aynı hasta için iki bot yanıt arası minimum süre
_response_lock = Lock()  # Thread safety için


def detect_intent(message: str) -> Optional[str]:
    """
    Mesajdan anahtar kelime tespit eder
    
    Args:
        message: Kullanıcı mesajı
        
    Returns:
        Tespit edilen anahtar kelime veya None
    """
    message_lower = message.lower().strip()
    
    # Anahtar kelime eşleşmesi
    for keyword in KEYWORD_RESPONSES.keys():
        if keyword in message_lower:
            return keyword
    
    # FAQ pattern eşleşmesi
    for pattern in FAQ_PATTERNS.keys():
        if re.search(pattern, message_lower):
            return pattern
    
    return None


def generate_response(message: str, detected_language: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Mesaja otomatik yanıt üretir
    
    Args:
        message: Kullanıcı mesajı
        detected_language: Tespit edilen dil kodu
        
    Returns:
        (yanıt_metni, yanıt_tipi) tuple'ı
        yanıt_tipi: 'keyword', 'faq', 'fallback', 'none'
    """
    if not message or len(message.strip()) < 3:
        return None, 'none'
    
    # Anahtar kelime kontrolü
    intent = detect_intent(message)
    
    if intent and intent in KEYWORD_RESPONSES:
        return KEYWORD_RESPONSES[intent], 'keyword'
    
    # FAQ pattern kontrolü
    if intent and intent in FAQ_PATTERNS:
        return FAQ_PATTERNS[intent], 'faq'
    
    # Fallback yanıt (opsiyonel - her mesaja otomatik yanıt vermemek için kapatılabilir)
    # Şimdilik None döndürüyoruz, sadece tanımlı keyword/pattern'lere yanıt veriliyor
    return None, 'none'


def should_auto_respond(message: str, sender_is_staff: bool = False, patient_id: Optional[int] = None) -> bool:
    """
    Otomatik yanıt verilmeli mi kontrol eder
    
    Args:
        message: Mesaj içeriği
        sender_is_staff: Gönderen personel mi?
        
    Returns:
        True ise bot yanıt vermeli
    """
    # Personel mesajlarına bot yanıt vermez
    if sender_is_staff:
        return False
    
    # Çok kısa mesajları atla
    if len(message.strip()) < 5:
        return False
    
    # Anahtar kelime veya pattern varsa yanıt ver
    intent = detect_intent(message)
    if not intent:
        return False

    # Throttle: Aynı hastaya çok sık bot yanıtı verme (Thread-safe)
    if patient_id is not None:
        with _response_lock:
            last = _LAST_RESPONSE.get(patient_id)
            now = datetime.utcnow()
            if last and now - last < _MIN_INTERVAL:
                logger.debug(f"Throttle aktif (patient_id={patient_id})")
                return False
            _LAST_RESPONSE[patient_id] = now
    return True


def get_chatbot_signature() -> str:
    """Chatbot imzası"""
    return '\n\n🤖 _Otomatik yanıt - Koordinatörümüz kısa süre içinde size dönüş yapacaktır._'
