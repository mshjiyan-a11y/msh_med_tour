import os
import sys

# Ensure project root is on sys.path so `app` package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models.user import User

app = create_app()

USERNAME = 'admin'
EMAIL = 'admin@example.com'
PASSWORD = 'password'

with app.app_context():
    user = User.query.filter((User.username==USERNAME)|(User.email==EMAIL)).first()
    if user:
        print(f"User already exists: {user.username} ({user.email})")
    else:
        admin = User(username=USERNAME, email=EMAIL, role='admin')
        admin.set_password(PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"Created superadmin: {USERNAME} / {PASSWORD}")
