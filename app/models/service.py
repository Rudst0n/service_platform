from datetime import datetime
from app.extensions import db


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)

    request_number = db.Column(db.Integer, nullable=False)
    request_code = db.Column(db.String(20), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="orcamento")

    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", backref="services")
    company = db.relationship("Company", backref="services")
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    images = db.relationship("ServiceImage", backref="service", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Service {self.request_code} - {self.name}>"