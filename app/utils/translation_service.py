"""
Translation Service - Çeviri servisi soyutlaması
Gelecekte Google Translate API, DeepL vb. entegre edilebilir
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Desteklenen diller
SUPPORTED_LANGUAGES = {
    'tr': 'Türkçe',
    'en': 'English',
    'ar': 'العربية',
    'de': 'Deutsch',
    'fr': 'Français',
    'ru': 'Русский'
}


def detect_language(text: str) -> Optional[str]:
    """
    Metin dilini tespit eder
    
    Args:
        text: Dili tespit edilecek metin
        
    Returns:
        Dil kodu (örn: 'tr', 'en') veya None
    """
    if not text or len(text.strip()) < 3:
        return None
    
    try:
        from langdetect import detect
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else None
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return None


def translate_text(text: str, target_lang: str, source_lang: Optional[str] = None) -> Optional[str]:
    """
    Metni hedef dile çevirir
    
    Args:
        text: Çevrilecek metin
        target_lang: Hedef dil kodu
        source_lang: Kaynak dil (None ise otomatik tespit)
        
    Returns:
        Çevrilmiş metin veya None (hata durumunda)
    """
    if not text or not target_lang:
        return None
    
    # Aynı dile çeviri gereksiz
    if source_lang and source_lang == target_lang:
        return text
    
    try:
        # deep-translator kullanarak çeviri (Google Translate ücretsiz API)
        from deep_translator import GoogleTranslator
        
        translator = GoogleTranslator(source='auto' if not source_lang else source_lang, 
                                     target=target_lang)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.warning(f"Translation failed ({source_lang or 'auto'} -> {target_lang}): {e}")
        return None


def get_language_name(lang_code: str) -> str:
    """Dil kodunun okunabilir adını döner"""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code.upper())


def should_translate(source_lang: str, target_lang: str) -> bool:
    """Çeviri gerekli mi kontrol eder"""
    if not source_lang or not target_lang:
        return False
    return source_lang != target_lang and target_lang in SUPPORTED_LANGUAGES
