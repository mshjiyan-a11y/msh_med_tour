"""
Currency Service - Döviz kuru güncelleme servisi
External API entegrasyonu ve otomatik kur güncelleme
"""
import requests
from datetime import datetime, timedelta
import logging
from app import db, cache
from app.models.currency import CurrencyRate

logger = logging.getLogger(__name__)

# Desteklenen para birimleri
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'TRY', 'SAR', 'AED', 'KWD', 'QAR', 'BHD', 'OMR', 'JOD']

# API Endpoints
EXCHANGERATE_API_URL = 'https://api.exchangerate-api.com/v4/latest/{base}'
TCMB_API_URL = 'https://www.tcmb.gov.tr/kurlar/today.xml'  # TCMB XML


def fetch_rates_from_exchangerate_api(base_currency='USD'):
    """
    ExchangeRate-API'den kurları çek
    
    Args:
        base_currency: Base currency (default USD)
        
    Returns:
        dict: {target_currency: rate} veya None
    """
    try:
        url = EXCHANGERATE_API_URL.format(base=base_currency)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        rates = data.get('rates', {})
        
        logger.info(f"ExchangeRate API: {len(rates)} kur alındı (base: {base_currency})")
        return rates
        
    except Exception as e:
        logger.error(f"ExchangeRate API hatası: {e}")
        return None


def fetch_rates_from_tcmb():
    """
    TCMB XML'den TRY bazlı kurları çek
    
    Returns:
        dict: {currency: rate_to_try} veya None
    """
    try:
        import xml.etree.ElementTree as ET
        
        response = requests.get(TCMB_API_URL, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        rates = {}
        
        for currency_node in root.findall('.//Currency'):
            code = currency_node.get('CurrencyCode')
            forex_selling = currency_node.find('ForexSelling')
            
            if forex_selling is not None and forex_selling.text:
                try:
                    rate = float(forex_selling.text)
                    rates[code] = rate
                except ValueError:
                    continue
        
        logger.info(f"TCMB: {len(rates)} kur alındı")
        return rates
        
    except Exception as e:
        logger.error(f"TCMB API hatası: {e}")
        return None


def update_rates_for_distributor(distributor_id, source='exchangerate-api', base_currency='USD'):
    """
    Belirli bir distributor için kurları güncelle
    
    Args:
        distributor_id: Distributor ID
        source: API source ('exchangerate-api' or 'tcmb')
        base_currency: Base currency
        
    Returns:
        int: Güncellenen kur sayısı
    """
    if source == 'tcmb':
        rates = fetch_rates_from_tcmb()
        if not rates:
            return 0
        
        # TCMB gives rates in TRY, so base is TRY
        actual_base = 'TRY'
        updated_count = 0
        
        for target_currency, rate in rates.items():
            if target_currency not in SUPPORTED_CURRENCIES:
                continue
            
            # Rate from TCMB is: 1 [target] = X TRY
            # We store as: 1 TRY = (1/X) [target]
            try:
                inverse_rate = 1.0 / rate if rate != 0 else 0
                
                existing = CurrencyRate.query.filter_by(
                    distributor_id=distributor_id,
                    base_currency=actual_base,
                    target_currency=target_currency
                ).first()
                
                if existing:
                    existing.rate = inverse_rate
                    existing.last_updated = datetime.utcnow()
                    existing.source = source
                else:
                    new_rate = CurrencyRate(
                        distributor_id=distributor_id,
                        base_currency=actual_base,
                        target_currency=target_currency,
                        rate=inverse_rate,
                        source=source,
                        is_manual=False
                    )
                    db.session.add(new_rate)
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"TCMB kur kaydetme hatası ({target_currency}): {e}")
                continue
        
        db.session.commit()
        return updated_count
    
    else:
        # ExchangeRate-API
        rates = fetch_rates_from_exchangerate_api(base_currency)
        if not rates:
            return 0
        
        updated_count = 0
        
        for target_currency, rate in rates.items():
            if target_currency not in SUPPORTED_CURRENCIES or target_currency == base_currency:
                continue
            
            try:
                existing = CurrencyRate.query.filter_by(
                    distributor_id=distributor_id,
                    base_currency=base_currency,
                    target_currency=target_currency
                ).first()
                
                if existing:
                    existing.rate = rate
                    existing.last_updated = datetime.utcnow()
                    existing.source = source
                else:
                    new_rate = CurrencyRate(
                        distributor_id=distributor_id,
                        base_currency=base_currency,
                        target_currency=target_currency,
                        rate=rate,
                        source=source,
                        is_manual=False
                    )
                    db.session.add(new_rate)
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Kur kaydetme hatası ({target_currency}): {e}")
                continue
        
        db.session.commit()
        return updated_count


def update_all_distributors():
    """Tüm distributorlar için kurları güncelle"""
    from app.models.distributor import Distributor
    
    distributors = Distributor.query.filter_by(is_active=True).all()
    total_updated = 0
    
    for dist in distributors:
        try:
            # Get base currency from settings
            from app.models.settings import AppSettings
            settings = AppSettings.get(dist.id)
            base = getattr(settings, 'base_currency', 'USD')
            source = getattr(settings, 'currency_api_source', 'exchangerate-api')
            
            count = update_rates_for_distributor(dist.id, source=source, base_currency=base)
            total_updated += count
            logger.info(f"Distributor {dist.id}: {count} kur güncellendi")
            
        except Exception as e:
            logger.error(f"Distributor {dist.id} kur güncellemesi başarısız: {e}")
            continue
    
    return total_updated


def get_cached_rate(distributor_id, from_currency, to_currency):
    """Cache'li kur sorgusu"""
    cache_key = f'rate_{distributor_id}_{from_currency}_{to_currency}'
    rate = cache.get(cache_key)
    
    if rate is None:
        rate = CurrencyRate.get_rate(distributor_id, from_currency, to_currency)
        if rate:
            cache.set(cache_key, rate, timeout=3600)  # 1 hour cache
    
    return rate


def format_price(amount, currency='USD', locale='tr'):
    """
    Fiyat formatlama
    
    Args:
        amount: Miktar
        currency: Para birimi kodu
        locale: Yerel dil ('tr', 'en', 'ar')
        
    Returns:
        str: Formatlanmış fiyat
    """
    if amount is None:
        return '-'
    
    # Currency symbols
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'TRY': '₺',
        'SAR': 'SR',
        'AED': 'AED',
        'KWD': 'KWD',
        'QAR': 'QAR',
        'BHD': 'BHD',
        'OMR': 'OMR',
        'JOD': 'JOD'
    }
    
    symbol = symbols.get(currency, currency)
    
    # Format with thousands separator
    if locale == 'tr':
        formatted = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{formatted} {symbol}"
    else:
        formatted = f"{amount:,.2f}"
        return f"{symbol}{formatted}"


def get_conversion_preview(amount, from_currency, to_currencies, distributor_id):
    """
    Çoklu para birimi dönüşüm önizlemesi
    
    Args:
        amount: Miktar
        from_currency: Kaynak para birimi
        to_currencies: Hedef para birimleri listesi
        distributor_id: Distributor ID
        
    Returns:
        dict: {currency: converted_amount}
    """
    preview = {}
    
    for target in to_currencies:
        converted = CurrencyRate.convert(amount, from_currency, target, distributor_id)
        if converted:
            preview[target] = converted
    
    return preview
