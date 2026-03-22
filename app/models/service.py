from datetime import datetime
from app.extensions import db


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("ServiceImage", backref="service", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Service {self.name}>"