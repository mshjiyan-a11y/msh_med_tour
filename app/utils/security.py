"""
Security utilities - Güvenlik yardımcı fonksiyonları
"""
import re
import hashlib
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Rate limiting basit in-memory cache (production'da Redis kullanılmalı)
_rate_limit_cache = {}


def sanitize_filename(filename: str) -> str:
    """
    Dosya adını güvenli hale getirir
    Zaten werkzeug.secure_filename kullanıyoruz ama ek kontroller
    """
    # Tehlikeli karakterleri kaldır
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    # Birden fazla noktayı tek noktaya indir
    filename = re.sub(r'\.+', '.', filename)
    # Boşlukları alt çizgi yap
    filename = filename.replace(' ', '_')
    # Maksimum uzunluk
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator: Rate limiting (basit implementation)
    
    Args:
        max_requests: Zaman penceresi içinde max istek sayısı
        window_seconds: Zaman penceresi (saniye)
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # İstemci IP'sini al
            client_ip = request.remote_addr or 'unknown'
            key = f"{f.__name__}:{client_ip}"
            
            now = datetime.utcnow()
            
            # Cache'i temizle (eski kayıtlar)
            expired_keys = [k for k, v in _rate_limit_cache.items() 
                          if now - v['reset_time'] > timedelta(seconds=window_seconds)]
            for k in expired_keys:
                del _rate_limit_cache[k]
            
            # Rate limit kontrolü
            if key in _rate_limit_cache:
                data = _rate_limit_cache[key]
                if data['count'] >= max_requests:
                    if now < data['reset_time']:
                        logger.warning(f"Rate limit exceeded for {key}")
                        return jsonify({
                            'error': 'Too many requests',
                            'retry_after': (data['reset_time'] - now).seconds
                        }), 429
                    else:
                        # Zaman penceresi doldu, sıfırla
                        _rate_limit_cache[key] = {
                            'count': 1,
                            'reset_time': now + timedelta(seconds=window_seconds)
                        }
                else:
                    _rate_limit_cache[key]['count'] += 1
            else:
                _rate_limit_cache[key] = {
                    'count': 1,
                    'reset_time': now + timedelta(seconds=window_seconds)
                }
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


def validate_file_mime(file, allowed_mimes: list) -> bool:
    """
    Dosya MIME tipini kontrol eder
    
    Args:
        file: werkzeug FileStorage objesi
        allowed_mimes: İzin verilen MIME tipleri listesi
        
    Returns:
        True ise geçerli
    """
    if not file or not file.content_type:
        return False
    
    return file.content_type in allowed_mimes


def hash_file_content(file_path: str) -> str:
    """
    Dosyanın SHA256 hash'ini hesaplar (içerik bütünlüğü için)
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        Hex hash string
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"File hashing failed: {e}")
        return None


# Encryption placeholder fonksiyonları
# Production'da cryptography kütüphanesi ile implement edilmeli

def encrypt_file(file_path: str, key: bytes = None) -> bool:
    """
    Dosyayı şifreler (PLACEHOLDER)
    
    TODO: Gerçek encryption implementasyonu:
    - Fernet (symmetric encryption) veya
    - AES-256-GCM ile dosya şifreleme
    - Key management (AWS KMS, Azure Key Vault, HashiCorp Vault)
    
    Args:
        file_path: Şifrelenecek dosya
        key: Encryption key (None ise otomatik generate)
        
    Returns:
        True ise başarılı
    """
    logger.info(f"PLACEHOLDER: File encryption for {file_path}")
    # Şimdilik sadece log
    return True


def decrypt_file(file_path: str, key: bytes) -> bool:
    """
    Dosyayı deşifreler (PLACEHOLDER)
    
    Args:
        file_path: Deşifrelenecek dosya
        key: Decryption key
        
    Returns:
        True ise başarılı
    """
    logger.info(f"PLACEHOLDER: File decryption for {file_path}")
    # Şimdilik sadece log
    return True


def get_encryption_key(document_id: int) -> bytes:
    """
    Belge için encryption key'i döner (PLACEHOLDER)
    
    TODO: Key management sistemi:
    - Her belge için unique key
    - Key'leri güvenli vault'ta sakla
    - Key rotation politikası
    
    Args:
        document_id: Belge ID
        
    Returns:
        Encryption key bytes
    """
    logger.info(f"PLACEHOLDER: Get encryption key for document {document_id}")
    # Şimdilik dummy key
    return b'dummy_encryption_key_32_bytes!!'


# MIME type whitelist (güvenli dosya tipleri)
SAFE_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain'
}


# Maksimum dosya boyutları (bytes)
MAX_FILE_SIZES = {
    'document': 10 * 1024 * 1024,      # 10MB
    'image': 5 * 1024 * 1024,           # 5MB
    'xray': 20 * 1024 * 1024,           # 20MB (büyük görüntüler)
    'default': 10 * 1024 * 1024         # 10MB
}
