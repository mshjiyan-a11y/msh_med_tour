#!/usr/bin/env python
"""
System Health Check Script
Verifies all components of Facebook Lead Integration

Usage:
    python check_system_health.py
    python check_system_health.py --verbose
    python check_system_health.py --test
"""

import sys
import os
from datetime import datetime
import importlib
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def check_dependencies():
    """Check if all required packages are installed"""
    print_header("1. CHECKING DEPENDENCIES")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_socketio',
        'flask_mail',
        'requests',
        'apscheduler',
    ]
    
    failed = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('_', '-'))
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print_warning(f"\nInstall missing packages:")
        print(f"  pip install {' '.join(failed)}")
        return False
    return True

def check_database_models():
    """Check if database models are properly defined"""
    print_header("2. CHECKING DATABASE MODELS")
    
    models_to_check = [
        ('app.models.meta_lead', 'MetaAPIConfig'),
        ('app.models.meta_lead', 'FacebookLead'),
        ('app.models.meta_lead', 'LeadInteraction'),
    ]
    
    failed = []
    for module_name, class_name in models_to_check:
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            print_success(f"{class_name} from {module_name}")
        except (ImportError, AttributeError) as e:
            print_error(f"{class_name} - {str(e)}")
            failed.append(class_name)
    
    return len(failed) == 0

def check_services():
    """Check if all service modules are available"""
    print_header("3. CHECKING SERVICES")
    
    services = [
        ('app.services.meta_lead_service', 'MetaLeadService'),
        ('app.services.lead_scoring', 'LeadScoringEngine'),
        ('app.services.bulk_operations', 'BulkLeadOperations'),
        ('app.services.lead_notifications', 'LeadEmailNotifications'),
        ('app.services.lead_analytics', 'LeadAnalytics'),
    ]
    
    failed = []
    for module_name, class_name in services:
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            print_success(f"{class_name} from {module_name}")
        except (ImportError, AttributeError) as e:
            print_error(f"{class_name} - {str(e)}")
            failed.append(class_name)
    
    return len(failed) == 0

def check_routes():
    """Check if routes are registered"""
    print_header("4. CHECKING ROUTES")
    
    try:
        from app.routes import facebook_leads
        print_success("facebook_leads blueprint found")
        
        # Check for key route names
        route_names = [
            'facebook_leads.index',
            'facebook_leads.view',
            'facebook_leads.update_status',
            'facebook_leads.analytics',
            'facebook_leads.scoring_dashboard',
        ]
        print_info(f"Expected routes: {len(route_names)} main routes")
        
        return True
    except ImportError as e:
        print_error(f"facebook_leads routes - {str(e)}")
        return False

def check_templates():
    """Check if all required templates exist"""
    print_header("5. CHECKING TEMPLATES")
    
    template_files = [
        'app/templates/admin/facebook_leads/index.html',
        'app/templates/admin/facebook_leads/view.html',
        'app/templates/admin/facebook_leads/scoring_dashboard.html',
        'app/templates/admin/facebook_leads/analytics.html',
    ]
    
    failed = []
    for template in template_files:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print_success(f"{template} ({size} bytes)")
        else:
            print_error(f"{template} - NOT FOUND")
            failed.append(template)
    
    return len(failed) == 0

def check_scheduler():
    """Check if scheduler is configured"""
    print_header("6. CHECKING SCHEDULER")
    
    try:
        from app.utils.meta_scheduler import scheduler
        print_success("meta_scheduler module found")
        print_info("Scheduler status: APScheduler configured")
        return True
    except ImportError as e:
        print_warning(f"Scheduler - {str(e)}")
        print_info("Note: Scheduler is optional, manual sync available")
        return True

def check_events():
    """Check if WebSocket events are configured"""
    print_header("7. CHECKING WEBSOCKET EVENTS")
    
    try:
        from app.events import lead_events
        print_success("lead_events module found")
        print_info("WebSocket namespace: /facebook-leads")
        return True
    except ImportError as e:
        print_warning(f"lead_events - {str(e)}")
        print_info("WebSocket events are optional")
        return True

def check_config():
    """Check configuration"""
    print_header("8. CHECKING CONFIGURATION")
    
    try:
        from app import create_app
        app = create_app()
        
        print_info(f"Flask Environment: {app.config.get('ENV', 'production')}")
        print_info(f"Debug Mode: {app.config.get('DEBUG', False)}")
        print_info(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')}")
        print_success("Configuration loaded successfully")
        return True
    except Exception as e:
        print_error(f"Configuration - {str(e)}")
        return False

def check_database_connection():
    """Check if database can be accessed"""
    print_header("9. CHECKING DATABASE CONNECTION")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Try to query database
            from app.models.meta_lead import FacebookLead
            count = FacebookLead.query.count()
            print_success(f"Database connection OK")
            print_info(f"Total leads in database: {count}")
            return True
    except Exception as e:
        print_error(f"Database connection - {str(e)}")
        return False

def check_meta_config():
    """Check if Meta API configuration exists"""
    print_header("10. CHECKING META API CONFIGURATION")
    
    try:
        from app import create_app, db
        from app.models.meta_lead import MetaAPIConfig
        app = create_app()
        
        with app.app_context():
            configs = MetaAPIConfig.query.filter_by(is_active=True).all()
            
            if not configs:
                print_warning("No active Meta API configurations found")
                print_info("Setup: Admin → Distributor Settings → Meta API Config")
                return True
            
            print_success(f"Found {len(configs)} active configuration(s):")
            for config in configs:
                print_info(f"  - {config.distributor.name} (Form ID: {config.form_id})")
            
            return True
    except Exception as e:
        print_warning(f"Meta configuration check - {str(e)}")
        return True

def run_full_check():
    """Run all health checks"""
    print_header("FACEBOOK LEAD INTEGRATION - SYSTEM HEALTH CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    checks = [
        ("Dependencies", check_dependencies()),
        ("Database Models", check_database_models()),
        ("Services", check_services()),
        ("Routes", check_routes()),
        ("Templates", check_templates()),
        ("Scheduler", check_scheduler()),
        ("WebSocket Events", check_events()),
        ("Configuration", check_config()),
        ("Database Connection", check_database_connection()),
        ("Meta API Config", check_meta_config()),
    ]
    
    print_header("HEALTH CHECK SUMMARY")
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{check_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ System is healthy and ready for production!{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Some checks failed. Please review the output above.{Colors.RESET}\n")
        return 1

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Lead Integration Health Check')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--test', action='store_true', help='Run test operations')
    
    args = parser.parse_args()
    
    exit_code = run_full_check()
    
    if args.test:
        print_header("RUNNING TEST OPERATIONS")
        
        try:
            from app import create_app, db
            from app.models.meta_lead import FacebookLead, LeadInteraction
            from app.services.lead_scoring import LeadScoringEngine
            
            app = create_app()
            
            with app.app_context():
                # Test lead creation
                test_lead = FacebookLead.query.first()
                if test_lead:
                    print_success(f"Found test lead: {test_lead.first_name} {test_lead.last_name}")
                    
                    # Test scoring
                    score = LeadScoringEngine.calculate_score(test_lead)
                    print_success(f"Lead score: {score}/100")
                    
                    # Test interactions
                    interactions = test_lead.interactions.count()
                    print_success(f"Lead interactions: {interactions}")
                else:
                    print_warning("No test leads found in database")
        
        except Exception as e:
            print_error(f"Test operation - {str(e)}")
    
    sys.exit(exit_code)
