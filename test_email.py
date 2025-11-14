"""
Email Configuration Test Script
Run this to verify your SMTP settings are working correctly.
"""
from app import create_app, db
from app.models import Lead, Distributor
from app.utils.email import send_new_lead_notification
import sys

def test_email():
    """Test email configuration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("MSH Med Tour - Email Configuration Test")
        print("=" * 60)
        print()
        
        # Check SMTP settings
        print("📧 SMTP Configuration:")
        print(f"   Server: {app.config.get('MAIL_SERVER')}")
        print(f"   Port: {app.config.get('MAIL_PORT')}")
        print(f"   TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"   Username: {app.config.get('MAIL_USERNAME')}")
        print(f"   Password: {'*' * 8 if app.config.get('MAIL_PASSWORD') else 'NOT SET'}")
        print()
        
        # Validate configuration
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("❌ ERROR: MAIL_USERNAME or MAIL_PASSWORD not set in .env file")
            print()
            print("Please update your .env file with valid SMTP credentials:")
            print("   MAIL_USERNAME=your-email@gmail.com")
            print("   MAIL_PASSWORD=your-app-password")
            print()
            print("For Gmail:")
            print("   1. Go to https://myaccount.google.com/apppasswords")
            print("   2. Generate an App Password")
            print("   3. Copy the 16-character password to .env")
            return False
        
        # Get first distributor for testing
        distributor = Distributor.query.first()
        
        if not distributor:
            print("❌ ERROR: No distributor found in database")
            print("   Please create a distributor first")
            return False
        
        if not distributor.email:
            print(f"❌ ERROR: Distributor '{distributor.name}' has no email address")
            print("   Please set an email for the distributor")
            return False
        
        print(f"📨 Test Recipient: {distributor.email}")
        print()
        
        # Create a test lead
        test_lead = Lead(
            distributor_id=distributor.id,
            source='test',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            phone='+905551234567',
            interested_service='hair_transplant',
            message='This is a test lead created for email configuration testing.',
            status='new'
        )
        
        print("📤 Sending test email...")
        print()
        
        try:
            send_new_lead_notification(test_lead, distributor)
            print("✅ SUCCESS! Email sent successfully.")
            print()
            print(f"Check the inbox of: {distributor.email}")
            print()
            print("If you don't receive the email:")
            print("   1. Check spam/junk folder")
            print("   2. Verify SMTP credentials in .env")
            print("   3. For Gmail: Ensure App Password is used")
            print("   4. Check firewall allows port 587")
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to send email")
            print(f"   {str(e)}")
            print()
            print("Common issues:")
            print("   - Invalid SMTP credentials")
            print("   - Gmail: Using regular password instead of App Password")
            print("   - Firewall blocking port 587")
            print("   - SMTP server down or incorrect")
            return False

if __name__ == '__main__':
    success = test_email()
    sys.exit(0 if success else 1)
