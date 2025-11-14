"""Meta Lead Sync Scheduler - Handles automatic lead fetching from Meta"""

import logging
from datetime import datetime
from app import create_app, db
from app.models.meta_lead import MetaAPIConfig
from app.services.meta_lead_service import MetaLeadService

logger = logging.getLogger(__name__)


def sync_all_meta_leads():
    """Sync leads from all active Meta configurations"""
    try:
        app = create_app()
        with app.app_context():
            configs = MetaAPIConfig.query.filter_by(is_active=True).all()
            
            if not configs:
                logger.info("No active Meta configurations to sync")
                return
            
            logger.info(f"Starting sync for {len(configs)} Meta configurations")
            
            for config in configs:
                try:
                    logger.info(f"Syncing leads for distributor {config.distributor_id}...")
                    service = MetaLeadService(config)
                    result = service.sync_leads(limit=100)
                    
                    log_msg = f"Distributor {config.distributor_id}: {result['message']}"
                    if result['success']:
                        logger.info(f"✓ {log_msg} ({result['fetched']} fetched, {result['stored']} stored)")
                    else:
                        logger.warning(f"✗ {log_msg}")
                
                except Exception as e:
                    logger.error(f"Error syncing distributor {config.distributor_id}: {str(e)}")
                    try:
                        config.last_error = str(e)
                        db.session.commit()
                    except:
                        pass
            
            logger.info("Meta lead sync completed")
    
    except Exception as e:
        logger.error(f"Fatal error in sync_all_meta_leads: {str(e)}")


def setup_meta_scheduler():
    """Setup APScheduler for Meta lead sync"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        scheduler = BackgroundScheduler()
        
        # Add job: sync every 5 minutes
        job = scheduler.add_job(
            sync_all_meta_leads,
            IntervalTrigger(minutes=5),
            id='meta_lead_sync',
            name='Meta Lead Sync',
            replace_existing=True,
            misfire_grace_time=60
        )
        
        scheduler.start()
        logger.info("✓ Meta Lead Sync Scheduler started (5-minute interval)")
        return scheduler
    
    except ImportError:
        logger.warning("APScheduler not installed. Install with: pip install apscheduler")
        return None
    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")
        return None


if __name__ == '__main__':
    # For manual testing
    sync_all_meta_leads()
