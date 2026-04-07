from datetime import datetime

from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    def __repr__(self):
        return f"<Customer {self.name}>"