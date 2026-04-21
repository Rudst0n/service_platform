from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    cpf = db.Column(db.String(14), nullable=True)

    password_hash = db.Column(db.String(255), nullable=True)
    is_portal_active = db.Column(db.Boolean, nullable=False, default=False)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def has_portal_access(self):
        return self.is_portal_active and bool(self.password_hash)

    def __repr__(self):
        return f"<Customer {self.name}>"