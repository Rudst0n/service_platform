from datetime import datetime

from app.extensions import db


class CompanyStatus:
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

    ALL = {PENDING, ACTIVE, INACTIVE, BLOCKED}


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    plan = db.Column(db.String(50), nullable=False, default="starter")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(20), nullable=False, default=CompanyStatus.PENDING)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    trial_ends_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_access_allowed(self):
        return self.status == CompanyStatus.ACTIVE and self.is_active


    @property
    def has_active_trial(self):
        return self.trial_ends_at is not None and self.trial_ends_at >= datetime.utcnow()

    @property
    def trial_expired(self):
        return self.trial_ends_at is not None and self.trial_ends_at < datetime.utcnow()
