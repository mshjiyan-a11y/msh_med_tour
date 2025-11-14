"""
Scheduled Tasks - Otomatik periyodik işlemler
APScheduler ile günlük kur güncellemeleri
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

scheduler = None


def update_currency_rates_job():
    """Günlük kur güncelleme görevi"""
    try:
        from app.utils.currency_service import update_all_distributors
        
        logger.info("Otomatik kur güncelleme başlatıldı...")
        count = update_all_distributors()
        logger.info(f"Kur güncelleme tamamlandı: {count} kur güncellendi")
        
    except Exception as e:
        logger.error(f"Kur güncelleme hatası: {e}")


def init_scheduler(app):
    """
    Zamanlayıcıyı başlat
    
    Args:
        app: Flask app instance
    """
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = BackgroundScheduler(daemon=True)
    
    # Push app context for database access
    with app.app_context():
        # Günlük kur güncelleme (her gün saat 09:00'da)
        scheduler.add_job(
            func=lambda: app.app_context().push() or update_currency_rates_job(),
            trigger=CronTrigger(hour=9, minute=0),
            id='update_currency_rates',
            name='Otomatik Kur Güncelleme',
            replace_existing=True
        )
    
    scheduler.start()
    logger.info("Zamanlayıcı başlatıldı")
    
    return scheduler


def shutdown_scheduler():
    """Zamanlayıcıyı kapat"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Zamanlayıcı kapatıldı")
