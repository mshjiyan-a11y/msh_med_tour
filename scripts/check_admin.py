from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    u = User.query.filter_by(username='admin').first()
    if not u:
        print('No admin user found')
    else:
        print('admin username:', u.username)
        print('admin distributor_id:', u.distributor_id)
        print('admin.distributor repr:', getattr(u,'distributor', None))
