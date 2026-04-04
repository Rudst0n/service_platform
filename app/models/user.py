from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    system_role = db.Column(db.String(50), nullable=False, default='company_user')
    company_role = db.Column(db.String(50), nullable=False, default='admin_empresa')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)

    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref='users')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def reset_login_lock(self):
        self.failed_login_attempts = 0
        self.locked_until = None

    def register_failed_login(self, max_attempts, lock_minutes):
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1

        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lock_minutes)
            self.failed_login_attempts = 0

    @property
    def is_temporarily_locked(self):
        return bool(self.locked_until and self.locked_until > datetime.utcnow())


from datetime import timedelta