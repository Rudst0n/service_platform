from flask import current_app, has_app_context
from flask_login import current_user
from sqlalchemy.orm import sessionmaker

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
    if not action or not entity_type:
        return

    resolved_user_id = user_id
    resolved_company_id = company_id

    try:
        if current_user.is_authenticated:
            if resolved_user_id is None:
                resolved_user_id = current_user.id

            if resolved_company_id is None:
                resolved_company_id = current_user.company_id
    except Exception:
        pass

    session = None

    try:
        engine = db.engine
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        log = AuditLog(
            action=str(action).strip(),
            entity_type=str(entity_type).strip(),
            entity_id=entity_id,
            description=description.strip() if isinstance(description, str) else description,
            company_id=resolved_company_id,
            user_id=resolved_user_id,
        )

        session.add(log)
        session.commit()

    except Exception:
        if session is not None:
            session.rollback()

        if has_app_context():
            current_app.logger.exception("Falha ao registrar log de auditoria.")

    finally:
        if session is not None:
            session.close()