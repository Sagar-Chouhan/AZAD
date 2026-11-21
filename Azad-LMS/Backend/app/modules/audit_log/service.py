import json
from sqlalchemy.orm import Session

from app.modules.auth.model import User
from .model import AuditLog


def create_audit_log(
    db: Session,
    user: User,
    action: str,
    entity: str,
    entity_id: str | int | None = None,
    details: str | None = None,
):
    """
    Creates an audit log entry in system_activity_log.
    The session is not committed here, it should be committed by the calling service.
    """
    desc_str = details
    if isinstance(details, (dict, list)):
        desc_str = json.dumps(details)

    log_entry = AuditLog(
        user_id=getattr(user, "id", None),
        user_name=getattr(user, "name", None) or getattr(user, "email", None),
        role_name=getattr(user, "responsibility", None) or getattr(user, "role", None),
        action=action,
        resource_type=entity,
        resource_id=str(entity_id) if entity_id is not None else None,
        description=desc_str,
        source="web",
    )
    db.add(log_entry)
