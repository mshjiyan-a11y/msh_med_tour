from app import db
+from app.models import Notification, User
+from app.utils.email import send_email
+from flask import current_app
+from typing import List, Optional
+
+
+def create_notification(title: str,
+                        message: Optional[str] = None,
+                        level: str = 'info',
+                        ntype: str = 'general',
+                        link_url: Optional[str] = None,
+                        distributor_id: Optional[int] = None,
+                        user_id: Optional[int] = None,
+                        created_by: Optional[int] = None,
+                        channel: str = 'in_app') -> Notification:
+    n = Notification(
+        title=title,
+        message=message,
+        level=level,
+        ntype=ntype,
+        link_url=link_url,
+        distributor_id=distributor_id,
+        user_id=user_id,
+        created_by=created_by,
+        channel=channel
+    )
+    db.session.add(n)
+    return n
+
+
+def notify_users(user_ids: List[int], title: str, message: str = '', link_url: Optional[str] = None,
+                 level: str = 'info', ntype: str = 'general', distributor_id: Optional[int] = None,
+                 created_by: Optional[int] = None, channel: str = 'in_app'):
+    """Create notifications for multiple users and optionally send email."""
+    users = User.query.filter(User.id.in_(user_ids)).all()
+    emails = []
+    for u in users:
+        create_notification(title=title, message=message, level=level, ntype=ntype, link_url=link_url,
+                            distributor_id=distributor_id or u.distributor_id, user_id=u.id,
+                            created_by=created_by, channel=channel)
+        if channel in ('email', 'both') and u.email:
+            emails.append(u.email)
+    if emails:
+        try:
+            send_email(subject=title, recipients=emails, text_body=message or title, html_body=None)
+        except Exception as e:
+            current_app.logger.warning(f"E-posta bildirimi gönderilemedi: {e}")
+
+
+def notify_distributor_admins(distributor_id: int, title: str, message: str = '', link_url: Optional[str] = None,
+                              level: str = 'info', ntype: str = 'general', created_by: Optional[int] = None,
+                              channel: str = 'in_app'):
+    admins = User.query.filter_by(distributor_id=distributor_id).filter(User.role.in_(['admin', 'distributor'])).all()
+    if not admins:
+        return
+    notify_users([a.id for a in admins], title, message, link_url, level, ntype, distributor_id, created_by, channel)
