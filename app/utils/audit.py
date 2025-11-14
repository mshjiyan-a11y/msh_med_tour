from app import db
from app.models.audit import AuditLog

def log_change(distributor_id, user_id, action, entity_type, entity_id=None, field=None, old=None, new=None, encounter_id=None, note=None):
    """Generic audit logger.
    Parameters:
      distributor_id (int): owning distributor
      user_id (int|None): actor user id (may be None for system actions)
      action (str): create|update|delete
      entity_type (str): type of entity
      entity_id (str|int|None): identifier
      field (str|None): field name if granular change
      old/new (Any): old/new values; will cast to str
      encounter_id (int|None): related encounter
      note (str|None): extra context
    """
    try:
        audit = AuditLog(
            distributor_id=distributor_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            field=field,
            old_value=str(old) if old is not None else None,
            new_value=str(new) if new is not None else None,
            encounter_id=encounter_id,
            note=note
        )
        db.session.add(audit)
    except Exception:
        # Fail silently; don't break business flow due to audit failure
        pass

def persist_audit():
    """Commit audit entries. Separate so multiple logs can batch before commit."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()