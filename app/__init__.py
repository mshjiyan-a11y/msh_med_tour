from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel
from flask_caching import Cache
from flask_socketio import SocketIO
from config import Config
import logging

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
babel = Babel()
cache = Cache()
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    # Initialize SocketIO
    socketio.init_app(app)
    
    # Cache configuration
    app.config['CACHE_TYPE'] = 'SimpleCache'  # Use 'redis' for production with CACHE_REDIS_URL
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)

    # Login configuration
    login.login_view = 'auth.login'
    login.login_message = 'Lütfen giriş yapın.'
    login.login_message_category = 'info'

    # User loader function for Flask-Login
    from app.models.user import User
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Register blueprints
    from app.routes import auth, main, admin, api, leads, journey_routes, communication, patient_portal, currency, facebook_leads
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(leads.bp)
    app.register_blueprint(journey_routes.bp)
    app.register_blueprint(communication.bp)
    app.register_blueprint(patient_portal.bp)
    app.register_blueprint(currency.bp)
    app.register_blueprint(facebook_leads.bp)

    # Context processor: inject global app settings
    @app.context_processor
    def inject_app_settings():
        # Safe defaults to avoid UnboundLocalError in exceptional paths
        unread_count = 0
        notif_preview = []
        settings = None
        try:
            from app.models.settings import AppSettings
            settings = AppSettings.get()
            # Unread notifications count (lightweight) for current user
            from flask_login import current_user
            if getattr(current_user, 'is_authenticated', False):
                try:
                    from app.models.notification import Notification
                    # User-specific + broadcast (user_id is NULL) for their distributor/admin scope
                    q = Notification.query
                    # unread first
                    q = q.order_by(Notification.is_read.asc(), Notification.created_at.desc())
                    # Filter for distributor scope if user has distributor
                    if current_user.distributor_id:
                        q = q.filter(db.or_(Notification.distributor_id == current_user.distributor_id,
                                            Notification.distributor_id.is_(None)))
                    # For non-admin staff only show targeted or broadcast
                    if not current_user.is_admin():
                        q = q.filter(db.or_(Notification.user_id == current_user.id,
                                            Notification.user_id.is_(None)))
                    else:
                        # Admin: show all in distributor scope
                        pass
                    unread_count = q.filter(Notification.is_read == False).count()
                    notif_preview = q.limit(5).all()
                except Exception:
                    # If notifications table not ready or any failure, keep defaults
                    pass
        except Exception:
            # In case migrations are not applied yet, return defaults
            if settings is None:
                settings = type('S', (), {
                    'enable_hair': True,
                    'enable_teeth': True,
                    'enable_eye': True,
                    'enable_hotel': True,
                    'enable_leads': True,
                    'theme_color': '#7a001d',
                    'navbar_style': 'glass'
                })()
        return {'app_settings': settings, 'unread_notifications': unread_count, 'notif_preview': notif_preview}

    # Create database tables
    # Import socket events (register handlers)
    try:
        from app import socket_events  # noqa: F401
        from app.events import lead_events  # noqa: F401
    except Exception:
        # Failing silently prevents startup crash if file missing during initial migration phase
        pass
    
    # Initialize scheduler for background tasks (currency updates)
    try:
        from app.utils.scheduler import init_scheduler
        init_scheduler(app)
    except Exception as e:
        # Scheduler is optional; don't crash if APScheduler not installed
        logger = logging.getLogger(__name__)
        logger.warning(f"Scheduler başlatılamadı: {e}")

    return app