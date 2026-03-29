from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    system_role = db.Column(db.String(50), nullable=False, default="company_user")
    company_role = db.Column(db.String(50), nullable=False, default="admin_empresa")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    company = db.relationship("Company", backref="users")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)