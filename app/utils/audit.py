from datetime import datetime
from flask_login import current_user

from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(
    action,
    entity_type,
    entity_id=None,
    description=None,
    company_id=None,
    user_id=None
):
    try:
        resolved_user_id = user_id
        resolved_company_id = company_id

        if current_user.is_authenticated:
            resolved_user_id = resolved_user_id or current_user.id
            resolved_company_id = resolved_company_id or current_user.company_id

        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            company_id=resolved_company_id,
            user_id=resolved_user_id,
            created_at=datetime.utcnow()
        )

        db.session.add(log)

    except Exception:
        # nunca quebrar o sistema por causa de log
        pass